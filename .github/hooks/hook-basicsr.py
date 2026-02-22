"""PyInstaller hook for basicsr (Basic Super-Resolution)
Don't try to introspect - just force include what we know is needed
"""
from PyInstaller.utils.hooks import collect_data_files

# Initialize required hook attributes
binaries = []
excludedimports = []

# Force include these modules without trying to import them
hiddenimports = [
    'basicsr',
    'basicsr.archs',
    'basicsr.archs.rrdbnet_arch',
    'basicsr.data',
    'basicsr.metrics',
    'basicsr.losses',
    'basicsr.models',
    'basicsr.utils',
]

# Include .py source files so TorchScript can access them at runtime
try:
    datas = collect_data_files('basicsr', include_py_files=True)
except (ImportError, ModuleNotFoundError) as _e:
    print(f"[basicsr hook] Could not collect data files: {_e!r} — datas left empty")
    datas = []

print(f"[basicsr hook] Forced {len(hiddenimports)} modules (no introspection)")
