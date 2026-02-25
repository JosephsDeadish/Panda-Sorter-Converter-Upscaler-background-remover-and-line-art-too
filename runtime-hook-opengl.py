"""
Runtime hook: configure PyOpenGL for the frozen Windows EXE.

PyInstaller runs this file BEFORE application code starts.  On Windows,
ctypes.util.find_library() does not search the application directory
(where PyInstaller bundles opengl32.dll / freeglut.dll), so PyOpenGL
falls back to the raw DLL name and relies on the OS loader.  This hook:

1. Calls os.add_dll_directory() for the frozen app folder so the OS DLL
   loader can find any bundled OpenGL DLLs placed there by the build.
2. Sets PYOPENGL_PLATFORM_HANDLER to 'win32' so PyOpenGL does not try
   the Linux/EGL backends that would be missing in the Windows bundle.
3. Disables PyOpenGL-accelerate's C extension so any missing or
   incompatible opengl_accelerate build does not crash the process.
   We do this via a sys.modules stub inserted BEFORE OpenGL is imported,
   which is more reliable than setting OpenGL.USE_ACCELERATE after the
   fact (by the time the main module runs, OpenGL may already be cached).

This hook is a no-op on Linux and macOS (they find OpenGL via the system
loader without extra paths).
"""

import os
import sys
import types


def _configure_pyopengl() -> None:
    if not sys.platform.startswith('win'):
        return

    # 1. Tell Windows DLL loader to search the frozen app folder.
    #    This is required on Python 3.8+ where the DLL search path changed.
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        try:
            os.add_dll_directory(app_dir)
        except (AttributeError, OSError):
            pass
        mei = getattr(sys, '_MEIPASS', None)
        if mei and mei != app_dir:
            try:
                os.add_dll_directory(mei)
            except (AttributeError, OSError):
                pass
    # Always add System32 — opengl32.dll and glu32.dll live there.
    sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
    try:
        if os.path.isdir(sys32):
            os.add_dll_directory(sys32)
    except (AttributeError, OSError):
        pass

    # 2. Force the Win32 platform backend so PyOpenGL doesn't attempt GLX/EGL.
    if 'PYOPENGL_PLATFORM_HANDLER' not in os.environ:
        os.environ['PYOPENGL_PLATFORM_HANDLER'] = 'win32'

    # 3. Block opengl_accelerate BEFORE OpenGL is imported.
    #    Inserting a stub module into sys.modules prevents any real
    #    opengl_accelerate C extension from loading.  If the C extension
    #    is buggy or built against a different driver it can segfault; pure-
    #    Python mode (USE_ACCELERATE=False) is always safe and fast enough.
    _stub = types.ModuleType('opengl_accelerate')
    _stub.USE_ACCELERATE = False  # type: ignore[attr-defined]
    for _name in ('opengl_accelerate', 'OpenGL_accelerate',
                  'OpenGL.arrays.numpymodule'):
        if _name not in sys.modules:
            sys.modules[_name] = _stub  # type: ignore[assignment]

    # Also tell OpenGL directly if it's already imported (unlikely at hook
    # time, but belt-and-suspenders).
    try:
        import OpenGL
        OpenGL.USE_ACCELERATE = False
    except Exception:
        pass  # Not yet imported; the sys.modules stub above handles it.


_configure_pyopengl()
