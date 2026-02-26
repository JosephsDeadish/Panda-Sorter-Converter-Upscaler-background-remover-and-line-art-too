"""PyInstaller hook for Real-ESRGAN
Collects all required modules and .py source files.
TorchScript requires .py files at runtime (include_py_files=True).
"""
from PyInstaller.utils.hooks import collect_data_files

# Initialize required hook attributes
binaries = []
excludedimports = []

# Force include these modules without trying to import them.
# NOTE: RRDBNet lives in basicsr.archs.rrdbnet_arch, NOT realesrgan.archs.
# Listing realesrgan.archs.rrdbnet_arch would produce "not found" warnings;
# basicsr hook already covers basicsr.archs.rrdbnet_arch.
hiddenimports = [
    'realesrgan',
    'realesrgan.utils',
]

# Collect .py source files so TorchScript can call inspect.getsource() at runtime
try:
    datas = collect_data_files('realesrgan', include_py_files=True)
except (ImportError, Exception) as _e:
    print(f"[realesrgan hook] Could not collect data files: {_e!r} — datas left empty")
    datas = []

print(f"[realesrgan hook] Forced {len(hiddenimports)} modules, {len(datas)} data files")
