"""
PyInstaller pre-safe-import hook for rembg.

This file MUST be named ``rembg.py`` (not ``hook-rembg.py``).
PyInstaller's pre_safe_import_module mechanism looks for files named after
the target module (without any ``hook-`` prefix) in a ``pre_safe_import_module/``
subdirectory within the hookspath.

This hook runs BEFORE rembg is imported during PyInstaller's analysis phase.
It patches sys.exit() to prevent rembg.bg from calling sys.exit(1) when
onnxruntime fails to initialise its DLL in the isolated analysis subprocess.

NOTE: rembg is listed in the ``excludes`` parameter of the spec files
(build_spec_onefolder.spec) so this hook normally does NOT run during a
standard build.  It is kept here as a safety net in case rembg is ever
re-enabled in the spec.

Author: Dead On The Inside / JosephsDeadish
"""

import sys


def pre_safe_import_module(api):  # noqa: ARG001 - api not used
    """
    Patches sys.exit() so rembg.bg's import-time sys.exit(1) call (triggered
    when onnxruntime DLL initialisation fails) raises SystemExit instead of
    terminating the PyInstaller analysis process.
    """
    _original_exit = sys.exit

    def _patched_exit(code=0):
        sys.exit = _original_exit  # restore before raising so the hook can re-run cleanly
        raise SystemExit(code)

    sys.exit = _patched_exit
