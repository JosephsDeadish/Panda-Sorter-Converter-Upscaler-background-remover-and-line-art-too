"""
GPU Detection and Device Information Module
Enhanced GPU detection with multiple vendor support and fallback handling
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import platform
import subprocess
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GPUVendor(Enum):
    """GPU vendor identifiers."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


@dataclass
class GPUDevice:
    """
    Information about a detected GPU device.
    
    Attributes:
        vendor: GPU vendor (NVIDIA, AMD, Intel, etc.)
        name: Full device name
        memory_mb: Total memory in MB (if available)
        driver_version: Driver version (if available)
        compute_capability: Compute capability (if available, NVIDIA)
        pci_id: PCI device ID (if available)
        index: Device index for multi-GPU systems
        is_primary: Whether this is the primary/default GPU
    """
    vendor: GPUVendor
    name: str
    memory_mb: Optional[int] = None
    driver_version: Optional[str] = None
    compute_capability: Optional[str] = None
    pci_id: Optional[str] = None
    index: int = 0
    is_primary: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vendor": self.vendor.value,
            "name": self.name,
            "memory_mb": self.memory_mb,
            "driver_version": self.driver_version,
            "compute_capability": self.compute_capability,
            "pci_id": self.pci_id,
            "index": self.index,
            "is_primary": self.is_primary
        }
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        parts = [self.name]
        if self.memory_mb:
            parts.append(f"{self.memory_mb}MB")
        if self.driver_version:
            parts.append(f"Driver: {self.driver_version}")
        return " | ".join(parts)


class GPUDetector:
    """
    Comprehensive GPU detection with multiple vendor support.
    
    Features:
    - NVIDIA GPU detection (nvidia-smi, CUDA, PyTorch)
    - AMD GPU detection (rocm-smi, OpenCL)
    - Intel GPU detection (OpenCL, Level Zero)
    - Apple Silicon detection (Metal)
    - Multiple GPU handling
    - Robust fallback mechanisms
    - Proper device name parsing
    """
    
    def __init__(self):
        """Initialize GPU detector."""
        self._devices: List[GPUDevice] = []
        self._detection_methods = {
            "nvidia": [
                self._detect_nvidia_smi,
                self._detect_nvidia_cuda,
                self._detect_nvidia_pytorch
            ],
            "amd": [
                self._detect_amd_rocm,
                self._detect_amd_opencl
            ],
            "intel": [
                self._detect_intel_opencl,
                self._detect_intel_vulkan
            ],
            "apple": [
                self._detect_apple_metal
            ]
        }
    
    def detect_gpus(self) -> List[GPUDevice]:
        """
        Detect all available GPUs.
        
        Returns:
            List of detected GPU devices
        """
        self._devices = []
        
        # Try detection methods for each vendor
        for vendor, methods in self._detection_methods.items():
            for method in methods:
                try:
                    detected = method()
                    if detected:
                        self._devices.extend(detected)
                        break  # Stop trying other methods for this vendor
                except Exception as e:
                    logger.debug(f"Detection method {method.__name__} failed: {e}")
        
        # If no GPUs detected, try generic fallback
        if not self._devices:
            self._devices = self._generic_fallback()
        
        # Set primary GPU
        if self._devices:
            self._devices[0].is_primary = True
        
        logger.info(f"Detected {len(self._devices)} GPU(s)")
        for gpu in self._devices:
            logger.info(f"  GPU {gpu.index}: {gpu}")
        
        return self._devices
    
    def get_devices(self) -> List[GPUDevice]:
        """
        Get detected GPU devices (call detect_gpus first).
        
        Returns:
            List of detected GPU devices
        """
        return self._devices
    
    def get_primary_device(self) -> Optional[GPUDevice]:
        """
        Get the primary/default GPU device.
        
        Returns:
            Primary GPU device or None if no GPUs detected
        """
        for device in self._devices:
            if device.is_primary:
                return device
        return self._devices[0] if self._devices else None
    
    def get_best_device(self) -> Optional[GPUDevice]:
        """
        Get the best GPU device based on memory and capabilities.
        
        Returns:
            Best GPU device or None if no GPUs detected
        """
        if not self._devices:
            return None
        
        # Sort by memory (highest first), then by index
        sorted_devices = sorted(
            self._devices,
            key=lambda d: (d.memory_mb or 0, -d.index),
            reverse=True
        )
        return sorted_devices[0]
    
    # NVIDIA Detection Methods
    
    def _detect_nvidia_smi(self) -> List[GPUDevice]:
        """Detect NVIDIA GPUs using nvidia-smi."""
        try:
            # Query GPU information
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version,pci.device_id",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            devices = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    index = int(parts[0])
                    name = self._parse_nvidia_name(parts[1])
                    # Round memory to nearest MB to avoid precision loss
                    memory_mb = round(float(parts[2])) if len(parts) > 2 and parts[2] else None
                    driver = parts[3] if len(parts) > 3 else None
                    pci_id = parts[4] if len(parts) > 4 else None
                    
                    devices.append(GPUDevice(
                        vendor=GPUVendor.NVIDIA,
                        name=name,
                        memory_mb=memory_mb,
                        driver_version=driver,
                        pci_id=pci_id,
                        index=index
                    ))
            
            # Try to get compute capability
            self._add_nvidia_compute_capability(devices)
            
            return devices
            
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            logger.debug(f"nvidia-smi detection failed: {e}")
            return []
    
    def _detect_nvidia_cuda(self) -> List[GPUDevice]:
        """Detect NVIDIA GPUs using CUDA."""
        try:
            import torch
            if not torch.cuda.is_available():
                return []
            
            devices = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                name = self._parse_nvidia_name(props.name)
                memory_mb = props.total_memory // (1024 * 1024)
                compute_cap = f"{props.major}.{props.minor}"
                
                devices.append(GPUDevice(
                    vendor=GPUVendor.NVIDIA,
                    name=name,
                    memory_mb=memory_mb,
                    compute_capability=compute_cap,
                    index=i
                ))
            
            return devices
            
        except (ImportError, Exception) as e:
            logger.debug(f"CUDA detection failed: {e}")
            return []
    
    def _detect_nvidia_pytorch(self) -> List[GPUDevice]:
        """Detect NVIDIA GPUs using PyTorch (simpler fallback)."""
        try:
            import torch
            if torch.cuda.is_available():
                # Simple detection - just report presence
                device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "NVIDIA GPU"
                return [GPUDevice(
                    vendor=GPUVendor.NVIDIA,
                    name=self._parse_nvidia_name(device_name),
                    index=0
                )]
        except Exception as e:
            logger.debug(f"PyTorch CUDA detection failed: {e}")
        return []
    
    def _add_nvidia_compute_capability(self, devices: List[GPUDevice]) -> None:
        """Add compute capability to NVIDIA devices if not already set."""
        try:
            import torch
            if not torch.cuda.is_available():
                return
            
            for device in devices:
                if device.vendor == GPUVendor.NVIDIA and not device.compute_capability:
                    if device.index < torch.cuda.device_count():
                        props = torch.cuda.get_device_properties(device.index)
                        device.compute_capability = f"{props.major}.{props.minor}"
        except Exception:
            pass
    
    def _parse_nvidia_name(self, raw_name: str) -> str:
        """
        Parse and clean NVIDIA GPU name.
        
        Examples:
            "NVIDIA GeForce RTX 3080" -> "GeForce RTX 3080"
            "GeForce RTX 3080" -> "GeForce RTX 3080"
            "Tesla V100-SXM2-32GB" -> "Tesla V100-SXM2 (32GB)"
        """
        name = raw_name.strip()
        
        # Remove "NVIDIA" prefix if present
        name = re.sub(r'^NVIDIA\s+', '', name, flags=re.IGNORECASE)
        
        # Clean up memory suffix (e.g., "Tesla V100-SXM2-32GB" -> "Tesla V100-SXM2 (32GB)")
        memory_match = re.search(r'-(\d+)GB$', name)
        if memory_match:
            memory_size = memory_match.group(1)
            name = re.sub(r'-\d+GB$', f' ({memory_size}GB)', name)
        
        return name
    
    # AMD Detection Methods
    
    def _detect_amd_rocm(self) -> List[GPUDevice]:
        """Detect AMD GPUs using ROCm (rocm-smi)."""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            devices = []
            # Parse rocm-smi output
            for line in result.stdout.split('\n'):
                if 'GPU' in line and ':' in line:
                    # Extract GPU index and name
                    match = re.search(r'GPU\[(\d+)\]\s*:\s*(.+)', line)
                    if match:
                        index = int(match.group(1))
                        name = self._parse_amd_name(match.group(2).strip())
                        devices.append(GPUDevice(
                            vendor=GPUVendor.AMD,
                            name=name,
                            index=index
                        ))
            
            return devices
            
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            logger.debug(f"rocm-smi detection failed: {e}")
            return []
    
    def _detect_amd_opencl(self) -> List[GPUDevice]:
        """Detect AMD GPUs using OpenCL."""
        try:
            import pyopencl as cl
            devices = []
            
            for platform in cl.get_platforms():
                if 'AMD' in platform.name or 'Radeon' in platform.name:
                    for idx, device in enumerate(platform.get_devices()):
                        if device.type == cl.device_type.GPU:
                            name = self._parse_amd_name(device.name)
                            memory_mb = device.global_mem_size // (1024 * 1024)
                            
                            devices.append(GPUDevice(
                                vendor=GPUVendor.AMD,
                                name=name,
                                memory_mb=memory_mb,
                                driver_version=device.driver_version,
                                index=idx
                            ))
            
            return devices
            
        except (ImportError, Exception) as e:
            logger.debug(f"AMD OpenCL detection failed: {e}")
            return []
    
    def _parse_amd_name(self, raw_name: str) -> str:
        """
        Parse and clean AMD GPU name.
        
        Examples:
            "AMD Radeon RX 6800 XT" -> "Radeon RX 6800 XT"
            "Radeon RX 580" -> "Radeon RX 580"
        """
        name = raw_name.strip()
        
        # Remove "AMD" prefix if present
        name = re.sub(r'^AMD\s+', '', name, flags=re.IGNORECASE)
        
        return name
    
    # Intel Detection Methods
    
    def _detect_intel_opencl(self) -> List[GPUDevice]:
        """Detect Intel GPUs using OpenCL."""
        try:
            import pyopencl as cl
            devices = []
            
            for platform in cl.get_platforms():
                if 'Intel' in platform.name:
                    for idx, device in enumerate(platform.get_devices()):
                        if device.type == cl.device_type.GPU:
                            name = self._parse_intel_name(device.name)
                            memory_mb = device.global_mem_size // (1024 * 1024)
                            
                            devices.append(GPUDevice(
                                vendor=GPUVendor.INTEL,
                                name=name,
                                memory_mb=memory_mb,
                                driver_version=device.driver_version,
                                index=idx
                            ))
            
            return devices
            
        except (ImportError, Exception) as e:
            logger.debug(f"Intel OpenCL detection failed: {e}")
            return []
    
    def _detect_intel_vulkan(self) -> List[GPUDevice]:
        """Detect Intel GPUs using Vulkan (fallback)."""
        # TODO: Implement Vulkan detection if needed
        return []
    
    def _parse_intel_name(self, raw_name: str) -> str:
        """
        Parse and clean Intel GPU name.
        
        Examples:
            "Intel(R) UHD Graphics 630" -> "UHD Graphics 630"
            "Intel(R) Iris(R) Xe Graphics" -> "Iris Xe Graphics"
        """
        name = raw_name.strip()
        
        # Remove "Intel(R)" prefix and cleanup
        name = re.sub(r'^Intel\(R\)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\(R\)', '', name)
        name = re.sub(r'\(TM\)', '', name)
        name = re.sub(r'\s+', ' ', name)  # Normalize spaces
        
        return name.strip()
    
    # Apple Detection Methods
    
    def _detect_apple_metal(self) -> List[GPUDevice]:
        """Detect Apple Silicon GPUs (Metal)."""
        if platform.system() != 'Darwin':
            return []
        
        try:
            # Try to detect Apple Silicon
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Use flexible regex to match any M-series chip (M1, M2, M3, M4, etc.)
            if 'Apple' in result.stdout and re.search(r'M\d+', result.stdout):
                # Extract chip name
                chip_match = re.search(r'Apple (M\d+[^\s]*)', result.stdout)
                chip_name = chip_match.group(1) if chip_match else "Apple Silicon"
                
                return [GPUDevice(
                    vendor=GPUVendor.APPLE,
                    name=f"Apple {chip_name} GPU",
                    index=0
                )]
        
        except Exception as e:
            logger.debug(f"Apple Metal detection failed: {e}")
        
        return []
    
    # Generic Fallback
    
    def _generic_fallback(self) -> List[GPUDevice]:
        """Generic fallback when no specific detection works."""
        system = platform.system()
        
        # Try to get some basic info from system
        gpu_name = "Unknown GPU"
        vendor = GPUVendor.UNKNOWN
        
        try:
            # Try lspci on Linux
            if system == "Linux":
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or '3D' in line:
                        # Extract GPU info
                        gpu_info = line.split(':', 1)[1].strip() if ':' in line else line
                        
                        # Detect vendor
                        if 'NVIDIA' in gpu_info or 'GeForce' in gpu_info:
                            vendor = GPUVendor.NVIDIA
                            gpu_name = self._parse_nvidia_name(gpu_info)
                        elif 'AMD' in gpu_info or 'Radeon' in gpu_info:
                            vendor = GPUVendor.AMD
                            gpu_name = self._parse_amd_name(gpu_info)
                        elif 'Intel' in gpu_info:
                            vendor = GPUVendor.INTEL
                            gpu_name = self._parse_intel_name(gpu_info)
                        else:
                            gpu_name = gpu_info
                        
                        break
        
        except Exception as e:
            logger.debug(f"Generic fallback detection failed: {e}")
        
        # Return a generic device
        return [GPUDevice(
            vendor=vendor,
            name=gpu_name,
            index=0
        )]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all detected GPUs.
        
        Returns:
            Dictionary with GPU summary information
        """
        return {
            "count": len(self._devices),
            "primary": self.get_primary_device().to_dict() if self.get_primary_device() else None,
            "devices": [d.to_dict() for d in self._devices],
            "has_nvidia": any(d.vendor == GPUVendor.NVIDIA for d in self._devices),
            "has_amd": any(d.vendor == GPUVendor.AMD for d in self._devices),
            "has_intel": any(d.vendor == GPUVendor.INTEL for d in self._devices),
            "has_apple": any(d.vendor == GPUVendor.APPLE for d in self._devices),
            "total_memory_mb": sum(d.memory_mb or 0 for d in self._devices)
        }
