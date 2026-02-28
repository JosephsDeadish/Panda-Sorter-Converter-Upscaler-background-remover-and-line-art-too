"""
PyInstaller hook for NumPy.

NumPy ships compiled binary extensions (.pyd on Windows, .so on Linux/macOS)
and, in NumPy 2.x, internal DLLs (e.g. _core .pyd files, BLAS/LAPACK .dll on
Windows wheels).  PyInstaller's built-in hook usually handles most of this, but
in our project we override the hooks path, so PyInstaller may prefer our hook
over its own.  This hook therefore does the full job:

1. collect_submodules   — every importable numpy name (lazy sub-packages)
2. collect_data_files   — .pyi stubs + any non-Python data bundled with numpy
3. collect_dynamic_libs — .pyd/.so/.dll compiled extensions (BLAS etc.)
4. Explicit hidden imports for submodules PyInstaller's static analyser misses
   due to lazy imports or conditional imports inside numpy itself.

NumPy 2.x notes
---------------
* ``numpy.core`` is now a thin compatibility shim over ``numpy._core``.
  Both need to be collected so that code importing ``numpy.core.multiarray``
  etc. still works after freezing.
* The random BitGenerators (MT19937, PCG64, …) are imported lazily and are
  missed by static analysis.
* ``numpy.f2py``, ``numpy.distutils``, and ``numpy.testing`` are optional but
  cheap to include.

Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs,
    collect_all,
)

# ── 1. collect_all: submodules + data files + binaries in one call ───────────
# collect_all is the recommended approach for packages with binary extensions.
# It calls collect_submodules, collect_data_files, and collect_dynamic_libs
# internally and handles edge cases that calling them separately may miss.
try:
    _all_datas, _all_binaries, _all_hiddenimports = collect_all('numpy')
    datas    = _all_datas
    binaries = _all_binaries
    hiddenimports = _all_hiddenimports
except Exception:
    # Fallback if collect_all is unavailable (older PyInstaller versions)
    datas    = collect_data_files('numpy')
    binaries = collect_dynamic_libs('numpy')
    hiddenimports = []

# ── 2. Ensure all submodules are included ────────────────────────────────────
hiddenimports += collect_submodules('numpy')

# ── 4. Explicit hidden imports not caught by static analysis ─────────────────
# These are imported conditionally or via __import__ inside numpy itself.
hiddenimports += [
    # Core public API
    'numpy',
    'numpy.core',
    'numpy.core.multiarray',
    'numpy.core.umath',
    'numpy.core.fromnumeric',
    'numpy.core.numeric',
    'numpy.core.numerictypes',
    'numpy.core.defchararray',
    'numpy.core.records',
    'numpy.core.memmap',
    'numpy.core.function_base',
    'numpy.core.machar',
    'numpy.core.getlimits',
    'numpy.core.shape_base',
    'numpy.core.einsumfunc',
    # NumPy 2.x — numpy._core replaces numpy.core internally
    'numpy._core',
    'numpy._core.multiarray',
    'numpy._core.umath',
    'numpy._core.fromnumeric',
    'numpy._core.numeric',
    'numpy._core.numerictypes',
    'numpy._core.defchararray',
    'numpy._core.records',
    'numpy._core.memmap',
    'numpy._core.function_base',
    'numpy._core.getlimits',
    'numpy._core.shape_base',
    'numpy._core.einsumfunc',
    'numpy._core.arrayprint',
    'numpy._core.arrayfunction_utils',
    # Math / linear-algebra
    'numpy.linalg',
    'numpy.linalg.lapack_lite',
    'numpy.linalg._umath_linalg',
    # Random
    'numpy.random',
    'numpy.random.mtrand',
    'numpy.random._common',
    'numpy.random._bounded_integers',
    'numpy.random._mt19937',
    'numpy.random._pcg64',
    'numpy.random._philox',
    'numpy.random._sfc64',
    'numpy.random._generator',
    'numpy.random._bit_generator',
    # FFT
    'numpy.fft',
    'numpy.fft._pocketfft',
    # Polynomial
    'numpy.polynomial',
    'numpy.polynomial.polynomial',
    'numpy.polynomial.chebyshev',
    'numpy.polynomial.legendre',
    'numpy.polynomial.hermite',
    'numpy.polynomial.hermite_e',
    'numpy.polynomial.laguerre',
    # Math utils
    'numpy.ma',
    'numpy.ma.core',
    'numpy.ma.extras',
    'numpy.matrixlib',
    'numpy.matrixlib.defmatrix',
    # Compat & testing (small, cheap to include)
    'numpy.compat',
    'numpy.testing',
    'numpy.testing._private',
    'numpy.f2py',
    # Lib — high-level wrappers
    'numpy.lib',
    'numpy.lib.stride_tricks',
    'numpy.lib.mixins',
    'numpy.lib.nanfunctions',
    'numpy.lib.shape_base',
    'numpy.lib.scimath',
    'numpy.lib.index_tricks',
    'numpy.lib.utils',
    'numpy.lib.arraysetops',
    'numpy.lib.function_base',
    'numpy.lib.histograms',
    'numpy.lib.twodim_base',
    'numpy.lib.ufunclike',
    'numpy.lib.arrayterator',
    'numpy.lib.npyio',
    'numpy.lib.format',
    'numpy.lib.type_check',
    'numpy.lib.financial',  # deprecated but may still be imported
    # Distutils (needed by some packages that import numpy.distutils at install
    # time; harmless to include)
    'numpy.distutils',
]

