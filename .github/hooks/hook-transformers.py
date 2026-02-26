"""
PyInstaller hook for HuggingFace transformers
Ensures transformers library and models are properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys

print("[transformers hook] Starting HuggingFace transformers collection...")

# Initialize required hook attributes
binaries = []
excludedimports = []

# Collect all transformers submodules
hiddenimports = collect_submodules('transformers')

# Add critical transformers modules explicitly
hiddenimports.extend([
    'transformers.models.clip',
    'transformers.models.clip.modeling_clip',
    'transformers.models.clip.configuration_clip',
    'transformers.models.clip.processing_clip',
    'transformers.models.clip.tokenization_clip',
])

# Collect transformers data files (model configs, tokenizers, etc.)
datas = collect_data_files('transformers', include_py_files=True)

print(f"[transformers hook] Collected {len(hiddenimports)} modules and {len(datas)} data files")
