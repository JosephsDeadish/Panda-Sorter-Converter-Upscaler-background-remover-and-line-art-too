"""PyInstaller hook for Real-ESRGAN
Don't try to introspect - just force include what we know is needed
"""

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

datas = []

print(f"[realesrgan hook] Forced {len(hiddenimports)} modules (no introspection)")
