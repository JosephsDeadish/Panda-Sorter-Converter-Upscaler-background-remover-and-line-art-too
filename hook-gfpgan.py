"""
PyInstaller hook for gfpgan (face / character restoration).

gfpgan depends on basicsr and facexlib.  This hook collects all gfpgan and
facexlib submodules so that face/character restoration is available in the
frozen exe when gfpgan is installed on the build machine.

Model weights (.pth files) are NOT bundled — they download at runtime via the
AI Model Manager on first use (to keep the EXE size reasonable).
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    collect_submodules('gfpgan') +
    collect_submodules('facexlib')
)

datas = (
    collect_data_files('gfpgan') +
    collect_data_files('facexlib')
)
