"""PyInstaller hook for basicsr (Basic Super-Resolution)
Don't try to introspect - just force include what we know is needed
"""

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

# Don't try to collect data files - just include the module
datas = []

print(f"[basicsr hook] Forced {len(hiddenimports)} modules (no introspection)")
