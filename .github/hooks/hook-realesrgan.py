"""PyInstaller hook for Real-ESRGAN
Collects all required modules and .py source files.
TorchScript requires .py files at runtime (include_py_files=True).
"""
from PyInstaller.utils.hooks import collect_data_files

# Initialize required hook attributes
binaries = []
excludedimports = []

# Force include these modules without trying to import them
hiddenimports = [
    'realesrgan',
    'realesrgan.archs',
    'realesrgan.archs.rrdbnet_arch',
    'realesrgan.data',
    'realesrgan.utils',
]

# Collect .py source files so TorchScript can call inspect.getsource() at runtime
try:
    datas = collect_data_files('realesrgan', include_py_files=True)
except (ImportError, Exception) as _e:
    print(f"[realesrgan hook] Could not collect data files: {_e!r} — datas left empty")
    datas = []

print(f"[realesrgan hook] Forced {len(hiddenimports)} modules, {len(datas)} data files")
