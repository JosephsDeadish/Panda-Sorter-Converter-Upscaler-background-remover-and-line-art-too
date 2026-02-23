"""
PyInstaller hook for faiss (faiss-cpu / faiss-gpu).

faiss is a C extension library for fast similarity search.  PyInstaller's
static analysis cannot discover its dynamic imports or native DLLs without
explicit help.

Used by: src/similarity/similarity_search.py (optional — app degrades
gracefully when faiss is absent; pure-numpy fallback is used).
"""
from __future__ import annotations

hiddenimports = [
    'faiss',
    'faiss.loader',       # main loader shim
    'faiss.extra_wrappers',
]

try:
    from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

    # Collect native .pyd / .so files (faiss wraps a C library)
    binaries = collect_dynamic_libs('faiss')
    hiddenimports += collect_submodules('faiss')
except Exception:
    binaries = []
