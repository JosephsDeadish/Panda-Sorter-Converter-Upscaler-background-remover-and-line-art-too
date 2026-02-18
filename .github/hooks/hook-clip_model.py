"""
PyInstaller hook for CLIP Model (src.vision_models.clip_model)
Ensures CLIP vision model and all dependencies are properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[clip_model hook] Starting CLIP model collection...")

# Initialize required hook attributes
datas = []
binaries = []
excludedimports = []

# Ensure core dependencies are available
hiddenimports = [
    # Core vision model
    'vision_models.clip_model',
    
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
    
    # Transformers - CLIP from HuggingFace
    'transformers',
    'transformers.models.clip',
    'transformers.models.clip.modeling_clip',
    'transformers.models.clip.configuration_clip',
    'transformers.models.clip.processing_clip',
    'transformers.models.clip.tokenization_clip',
    
    # Open CLIP - Alternative CLIP implementation
    'open_clip',
    'open_clip.model',
    'open_clip.transform',
    'open_clip.tokenizer',
    
    # Supporting libraries
    'numpy',
    'regex',
    'tokenizers',
    'safetensors',
    'huggingface_hub',
]

# Collect data files for transformers (model configs, tokenizers, etc.)
datas = []
try:
    datas.extend(collect_data_files('transformers', include_py_files=False))
    print(f"[clip_model hook] Collected transformers data files")
except Exception as e:
    print(f"[clip_model hook] WARNING: Could not collect transformers data: {e}")

try:
    datas.extend(collect_data_files('open_clip', include_py_files=False))
    print(f"[clip_model hook] Collected open_clip data files")
except Exception as e:
    print(f"[clip_model hook] WARNING: Could not collect open_clip data: {e}")

print(f"[clip_model hook] Collected {len(hiddenimports)} hidden imports and {len(datas)} data files")
print("[clip_model hook] CLIP model collection completed successfully")
