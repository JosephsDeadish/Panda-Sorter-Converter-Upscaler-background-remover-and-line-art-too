"""
PyInstaller hook for open_clip
Ensures OpenCLIP models are properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

print("[open_clip hook] Starting open_clip collection...")

# Collect all open_clip submodules
hiddenimports = collect_submodules('open_clip')

# Collect open_clip data files (model configs, etc.)
datas = collect_data_files('open_clip', include_py_files=False)

print(f"[open_clip hook] Collected {len(hiddenimports)} modules and {len(datas)} data files")
