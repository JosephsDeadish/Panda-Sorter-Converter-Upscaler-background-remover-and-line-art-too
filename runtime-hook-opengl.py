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
3. Disables PyOpenGL-accelerate's C extension if it is absent (avoids a
   confusing ImportError that would otherwise mask the real GL widget).

This hook is a no-op on Linux and macOS (they find OpenGL via the system
loader without extra paths).
"""

import os
import sys


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
            # add_dll_directory only exists on Python 3.8+; ignore on older builds
            pass
        # Also add _MEIPASS (the unpacked bundle dir for onefile builds)
        mei = getattr(sys, '_MEIPASS', None)
        if mei and mei != app_dir:
            try:
                os.add_dll_directory(mei)
            except (AttributeError, OSError):
                pass
        # Add System32 — opengl32.dll and glu32.dll live there on all modern Windows.
        # In a frozen EXE the default DLL search path may omit System32.
        sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
        try:
            if os.path.isdir(sys32):
                os.add_dll_directory(sys32)
        except (AttributeError, OSError):
            pass

    # 2. Force the Win32 platform backend so PyOpenGL doesn't attempt GLX/EGL.
    if 'PYOPENGL_PLATFORM_HANDLER' not in os.environ:
        os.environ['PYOPENGL_PLATFORM_HANDLER'] = 'win32'

    # 3. Suppress the PyOpenGL-accelerate ImportError if the C extension is
    #    absent — PyOpenGL degrades gracefully to pure-Python mode which works
    #    fine for the fixed-function GL pipeline used by the panda widget.
    try:
        import OpenGL
        OpenGL.USE_ACCELERATE = False  # prefer pure-Python arrays (always available)
    except Exception:
        pass  # OpenGL not yet importable at hook time (normal); setting env is enough


_configure_pyopengl()
