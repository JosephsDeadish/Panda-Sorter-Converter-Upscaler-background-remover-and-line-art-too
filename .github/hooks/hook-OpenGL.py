"""
PyInstaller hook for PyOpenGL (OpenGL package).

Ensures that the Windows OpenGL platform backend (opengl32.dll/freeglut DLLs)
and all required array / wrapper submodules are collected into the frozen EXE
so the 3-D panda widget (panda_widget_gl.py) works at runtime.

Why this is needed
------------------
PyInstaller's static analyser discovers only the submodules that are
explicitly imported in source code.  PyOpenGL uses a dynamic platform-loading
mechanism:  on Windows it loads ``OpenGL.platform.win32`` at import time via
``OpenGL.platform.__init__`` but that selection is driven by ``sys.platform``
and is invisible to the analyser.  Without this hook the Windows build ends up
with only ``OpenGL.platform.glx`` (Linux) and the panda widget raises
``ImportError: cannot import name 'win32'`` at startup.

Similarly, ``OpenGL.arrays`` lazy-loads array handler submodules (ctypesarrays,
numpymodule, etc.) that must be present in the bundle.
"""

from __future__ import annotations

import os
import sys
import glob

# ── Required by PyInstaller: must be module-level ─────────────────────────────
hiddenimports: list[str] = []
datas: list[tuple[str, str]] = []
binaries: list[tuple[str, str]] = []

# ── Hidden imports that PyInstaller's analyser misses ─────────────────────────

# Platform backend — select correct one for the *build* platform (== target
# platform in CI).  Include both so a cross-compiled build works too.
hiddenimports += [
    'OpenGL.platform.win32',        # Windows OpenGL backend
    'OpenGL.platform.darwin',       # macOS OpenGL backend
    'OpenGL.platform.glx',          # Linux/X11 OpenGL backend
    'OpenGL.platform.egl',          # EGL (headless/wayland) backend
    # Array handler submodules (chosen dynamically by OpenGL.arrays.__init__)
    'OpenGL.arrays.ctypesarrays',
    'OpenGL.arrays.ctypesparameters',
    'OpenGL.arrays.numpymodule',
    'OpenGL.arrays.numbers',
    'OpenGL.arrays.strings',
    'OpenGL.arrays.lists',
    'OpenGL.arrays.vbo',
    # GL extensions wrapper
    'OpenGL.GL.shaders',
    'OpenGL.GL.framebufferobjects',
    # GLU
    'OpenGL.GLU',
    # Accelerate C-extension (optional — present when PyOpenGL-accelerate is installed)
    'OpenGL.acceleratesupport',
]

# ── Collect native DLLs on Windows ───────────────────────────────────────────

if sys.platform == 'win32':
    try:
        import site
        import sysconfig

        search_paths: list[str] = []
        try:
            search_paths += site.getsitepackages()
        except AttributeError:
            pass  # not available in venv on older Python
        for _key in ('purelib', 'platlib'):
            _p = sysconfig.get_path(_key)
            if _p:
                search_paths.append(_p)

        _collected_dlls: set[str] = set()

        for sp in search_paths:
            opengl_dir = os.path.join(sp, 'OpenGL')
            if not os.path.isdir(opengl_dir):
                continue

            # Walk the entire OpenGL package directory for DLLs / PYD files.
            for root, _dirs, files in os.walk(opengl_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    flower = fname.lower()
                    if flower.endswith(('.dll', '.pyd')):
                        # Compute destination relative to the opengl_dir parent
                        rel = os.path.relpath(root, sp)
                        key = flower
                        if key not in _collected_dlls:
                            binaries.append((fpath, rel))
                            _collected_dlls.add(key)

            # Also look for freeglut DLLs placed alongside the OpenGL package
            for pattern in ('freeglut*.dll', 'glut*.dll'):
                for fpath in glob.glob(os.path.join(sp, pattern)):
                    fname = os.path.basename(fpath)
                    if fname.lower() not in _collected_dlls:
                        binaries.append((fpath, '.'))
                        _collected_dlls.add(fname.lower())

            print(f"[hook-OpenGL] Collected {len(_collected_dlls)} files from {opengl_dir} (first match)")
            break   # found the package; stop searching (first site-packages match used)

    except Exception as _exc:
        print(f"[hook-OpenGL] Warning: could not collect Windows OpenGL DLLs: {_exc}")

print(f"[hook-OpenGL] hiddenimports: {len(hiddenimports)}, "
      f"binaries: {len(binaries)}, datas: {len(datas)}")
