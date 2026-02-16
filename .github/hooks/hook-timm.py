"""
PyInstaller hook for timm (PyTorch Image Models)
Ensures timm model zoo is properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[timm hook] Starting timm collection...")

# Collect all timm submodules
hiddenimports = collect_submodules('timm')

# Collect timm data files (model configs, etc.)
datas = collect_data_files('timm', include_py_files=False)

print(f"[timm hook] Collected {len(hiddenimports)} modules and {len(datas)} data files")
