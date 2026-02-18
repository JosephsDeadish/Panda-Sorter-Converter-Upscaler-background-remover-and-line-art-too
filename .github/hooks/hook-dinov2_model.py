"""
PyInstaller hook for DINOv2 Model (src.vision_models.dinov2_model)
Ensures DINOv2 vision model and all dependencies are properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[dinov2_model hook] Starting DINOv2 model collection...")

# Initialize required hook attributes
datas = []
binaries = []
excludedimports = []

# Ensure core dependencies are available
hiddenimports = [
    # Core vision model
    'vision_models.dinov2_model',
    
    # PIL - CRITICAL for image loading
    'PIL',
    'PIL.Image',
    'PIL.ImageFile',
    'PIL._imaging',
    
    # PyTorch - CRITICAL for model inference
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'torch._C',
    'torchvision',
    'torchvision.transforms',
    
    # Timm - Required for DINOv2 models
    'timm',
    'timm.models',
    'timm.models.vision_transformer',
    
    # Supporting libraries
    'numpy',
    'huggingface_hub',
]

# Collect data files for timm (model configs, etc.)
datas = []
try:
    datas.extend(collect_data_files('timm', include_py_files=False))
    print(f"[dinov2_model hook] Collected timm data files")
except Exception as e:
    print(f"[dinov2_model hook] WARNING: Could not collect timm data: {e}")

print(f"[dinov2_model hook] Collected {len(hiddenimports)} hidden imports and {len(datas)} data files")
print("[dinov2_model hook] DINOv2 model collection completed successfully")
