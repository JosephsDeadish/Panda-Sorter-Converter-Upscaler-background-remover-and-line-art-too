"""
PyInstaller hook for rembg
Handles AI background removal tool and its dependencies

NOTE: rembg is listed in the `excludes` parameter of both spec files
(build_spec_onefolder.spec and build_spec_with_svg.spec) to prevent
a build-time crash: rembg.bg calls sys.exit(1) when onnxruntime fails
to initialise its DLL in PyInstaller's isolated analysis subprocesses.

Because rembg is in `excludes`, PyInstaller will NOT call this hook
during a normal build.  This file is kept here only as documentation
and as a fallback no-op in case a custom spec re-enables rembg.

onnxruntime DLLs are still collected via hook-onnxruntime.py.
"""

# rembg is excluded from the build - produce empty outputs so this hook
# is a no-op if it is ever called.
hiddenimports = []
datas = []
binaries = []
