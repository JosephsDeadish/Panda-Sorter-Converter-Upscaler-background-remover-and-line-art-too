"""
PyInstaller hook for timm (PyTorch Image Models)
Ensures timm model zoo is properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[timm hook] Starting timm collection...")

# Initialize required hook attributes
binaries = []
excludedimports = []

# Collect all timm submodules
hiddenimports = collect_submodules('timm')

# Collect timm data files AND Python source files.
# TorchScript requires access to the .py source files at runtime to compile
# model scripts.  Without include_py_files=True the frozen EXE raises:
#   "Can't get source for class 'timm.models.hrnet.ModuleInterface'"
# because PyInstaller compiles .py → .pyc but doesn't keep the raw sources.
datas = collect_data_files('timm', include_py_files=True)

print(f"[timm hook] Collected {len(hiddenimports)} modules and {len(datas)} data files")
