"""
Runtime hook: configure PyOpenGL for the frozen Windows EXE.

PyInstaller runs this file BEFORE application code starts.  On Windows,
ctypes.util.find_library() does not search the application directory
(where PyInstaller bundles opengl32.dll / freeglut.dll), so PyOpenGL
falls back to the raw DLL name and relies on the OS loader.  This hook:

1. Calls os.add_dll_directory() for the frozen app folder so the OS DLL
   loader can find any bundled OpenGL DLLs placed there by the build.
2. Sets QT_OPENGL=desktop so Qt uses native opengl32.dll, NOT ANGLE.
   ANGLE only supports OpenGL ES — it rejects CompatibilityProfile calls
   (glShadeModel, glLightfv, glBegin/glEnd) with GL_INVALID_OPERATION,
   causing initializeGL() to fail and the 2D panda fallback to show.
3. Sets PYOPENGL_PLATFORM_HANDLER to 'win32' so PyOpenGL does not try
   the Linux/EGL backends that would be missing in the Windows bundle.
4. Disables PyOpenGL-accelerate's C extension so any missing or
   incompatible opengl_accelerate build does not crash the process.
5. Sets U2NET_HOME to app_data/models/ so rembg's new_session() finds
   the pre-bundled ONNX files without downloading again on first run.

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

    # 2. Force Qt to use native OpenGL (opengl32.dll) NOT ANGLE (Direct3D).
    #    ANGLE only supports OpenGL ES — it DOES NOT support CompatibilityProfile.
    #    Without this, glShadeModel/glLightfv/glBegin fail with GL_INVALID_OPERATION
    #    and the 3D panda's initializeGL() raises GLError, triggering the 2D fallback.
    #    QT_OPENGL=desktop forces native opengl32.dll which supports CompatibilityProfile
    #    on all modern Windows GPUs (NVIDIA, AMD, Intel HD 4000+).
    if 'QT_OPENGL' not in os.environ:
        os.environ['QT_OPENGL'] = 'desktop'

    # 3. Force the Win32 platform backend so PyOpenGL doesn't attempt GLX/EGL.
    if 'PYOPENGL_PLATFORM_HANDLER' not in os.environ:
        os.environ['PYOPENGL_PLATFORM_HANDLER'] = 'win32'

    # 4. Block opengl_accelerate BEFORE OpenGL is imported.
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

    # 5. Set Qt's AA_UseDesktopOpenGL application attribute.
    #    This is the C++-level equivalent of QT_OPENGL=desktop — more reliable
    #    than the env var alone because it is processed by Qt's platform plugin
    #    loader before ANGLE selection logic runs.
    #    Must be called before QApplication is constructed.
    try:
        from PyQt6.QtWidgets import QApplication as _QA
        from PyQt6.QtCore import Qt as _Qt
        _QA.setAttribute(_Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    except Exception:
        pass  # Qt not yet imported at hook time; main.py sets it too.


def _configure_rembg_home() -> None:
    """Point rembg at the app_data/models directory inside the frozen EXE bundle.

    rembg uses U2NET_HOME (or ~/.u2net/) to find ONNX model files.  In the
    frozen EXE, models are pre-bundled into dist/GameTextureSorter/app_data/models/.
    Setting U2NET_HOME here (before any imports run) ensures rembg's
    new_session() finds them without downloading again on first run.
    """
    if not getattr(sys, 'frozen', False):
        return  # source runs: let main.py handle this via config.get_data_dir()
    try:
        _exe_dir = os.path.dirname(sys.executable)
        _models_dir = os.path.join(_exe_dir, 'app_data', 'models')
        if 'U2NET_HOME' not in os.environ:
            os.environ['U2NET_HOME'] = _models_dir
    except Exception:
        pass  # Non-fatal: rembg will fall back to ~/.u2net/


_configure_pyopengl()
_configure_rembg_home()
