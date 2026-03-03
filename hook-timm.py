"""
PyInstaller hook for timm (PyTorch Image Models).

timm ships compiled binary extensions for some operations and uses JSON-based
model configuration files.  collect_all() in the spec handles binary collection,
but this hook ensures data files (config JSON, pretrained model metadata) are
also included so that timm.create_model() resolves model architecture names at
runtime without network access.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Full submodule tree — timm uses lazy imports extensively
hiddenimports = collect_submodules('timm')

# JSON model configs, pretrained metadata, version files
datas = collect_data_files('timm')
