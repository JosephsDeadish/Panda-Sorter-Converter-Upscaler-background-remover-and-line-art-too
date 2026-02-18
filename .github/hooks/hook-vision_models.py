"""
PyInstaller hook for Vision Models Package (src.vision_models)
Master hook for all vision models - ensures PIL, torch, and all dependencies
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[vision_models hook] Starting vision models package collection...")

# Initialize required hook attributes
datas = []
binaries = []
excludedimports = []

# Collect all vision_models submodules
hiddenimports = collect_submodules('vision_models')

# Ensure critical dependencies are included
critical_imports = [
    # Vision model modules
    'vision_models',
    'vision_models.clip_model',
    'vision_models.dinov2_model',
    'vision_models.efficientnet_model',
    'vision_models.vit_model',
    'vision_models.sam_model',
    
    # PIL - CRITICAL for all vision models
    'PIL',
    'PIL.Image',
    'PIL.ImageFile',
    'PIL._imaging',
    'PIL.PngImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.TiffImagePlugin',
    
    # PyTorch - CRITICAL for all vision models
    'torch',
    'torch._C',
    'torch.nn',
    'torch.nn.functional',
    'torch.cuda',
    'torchvision',
    'torchvision.transforms',
    
    # Transformers - for CLIP and other HuggingFace models
    'transformers',
    'transformers.models.clip',
    
    # Timm - for DINOv2 and other vision models
    'timm',
    'timm.models',
    
    # Open CLIP - alternative CLIP implementation
    'open_clip',
    
    # Supporting libraries
    'numpy',
    'regex',
    'tokenizers',
    'safetensors',
    'huggingface_hub',
]

# Add critical imports, avoiding duplicates
for imp in critical_imports:
    if imp not in hiddenimports:
        hiddenimports.append(imp)

# Collect data files for all vision model dependencies
datas = []

# Collect transformers data
try:
    datas.extend(collect_data_files('transformers', include_py_files=False))
    print(f"[vision_models hook] Collected transformers data files")
except Exception as e:
    print(f"[vision_models hook] WARNING: Could not collect transformers data: {e}")

# Collect timm data
try:
    datas.extend(collect_data_files('timm', include_py_files=False))
    print(f"[vision_models hook] Collected timm data files")
except Exception as e:
    print(f"[vision_models hook] WARNING: Could not collect timm data: {e}")

# Collect open_clip data
try:
    datas.extend(collect_data_files('open_clip', include_py_files=False))
    print(f"[vision_models hook] Collected open_clip data files")
except Exception as e:
    print(f"[vision_models hook] WARNING: Could not collect open_clip data: {e}")

print(f"[vision_models hook] Collected {len(hiddenimports)} hidden imports and {len(datas)} data files")
print("[vision_models hook] Vision models package collection completed successfully")
