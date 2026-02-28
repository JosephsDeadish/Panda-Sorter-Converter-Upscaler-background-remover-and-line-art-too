"""
Runtime hook for NumPy — frozen (PyInstaller) executables.

On Windows, NumPy ships its own BLAS/LAPACK DLLs (e.g. OpenBLAS, MKL) inside
the wheel.  When the application is frozen with PyInstaller, the numpy package
directory lives inside _MEIPASS.  If the numpy DLL directory is not on the DLL
search PATH, Windows will raise ``ImportError: DLL load failed`` when any
numpy compiled extension (numpy.core.multiarray, numpy.linalg, etc.) is
imported.

This hook runs *before* main.py and adds the numpy compiled-extension
directory to the Windows DLL search PATH so that the loader can find any
numpy-bundled BLAS/LAPACK DLLs at startup.

On Linux/macOS the linker uses RPATH embedded in the .so files, so no PATH
manipulation is needed there.

Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os

if getattr(sys, 'frozen', False):
    # We are running inside a PyInstaller bundle
    _meipass = sys._MEIPASS  # noqa: SLF001 (private, but standard PyInstaller API)

    # ── Windows: add numpy's DLL directories to the loader search path ───────
    if sys.platform == 'win32':
        import ctypes
        _numpy_dirs = [
            # NumPy 1.x layout
            os.path.join(_meipass, 'numpy', 'core'),
            os.path.join(_meipass, 'numpy', 'linalg'),
            os.path.join(_meipass, 'numpy', 'fft'),
            os.path.join(_meipass, 'numpy', 'random'),
            # NumPy 2.x layout
            os.path.join(_meipass, 'numpy', '_core'),
            os.path.join(_meipass, 'numpy', 'libs'),
            # OpenBLAS / MKL shipped alongside numpy wheel (Windows only)
            os.path.join(_meipass, 'numpy', '.libs'),
        ]
        for _d in _numpy_dirs:
            if os.path.isdir(_d):
                try:
                    # AddDllDirectory (Win 8+) is preferred over os.environ PATH
                    # because it affects the DLL loader directly.
                    ctypes.windll.kernel32.AddDllDirectory(_d)
                except OSError:
                    # Fall back to PATH manipulation on older Windows
                    os.environ['PATH'] = _d + os.pathsep + os.environ.get('PATH', '')

    # ── Pre-import numpy to verify it loads correctly ─────────────────────────
    # Doing this here (before the app starts) gives a clear error message
    # instead of a confusing crash mid-application.
    try:
        import numpy as _np  # noqa: F401
    except Exception as _e:
        import traceback as _tb
        print(
            f"[runtime-hook-numpy] WARNING: numpy failed to import in frozen exe: {_e}\n"
            f"{_tb.format_exc()}\n"
            "Array-based features (line art conversion, image processing, etc.) "
            "will fall back to pure-PIL paths."
        )

