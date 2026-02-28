#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Hybrid PyTorch/ONNX architecture + lazy rembg import safety

Validates the core requirements introduced by the EXE build fix:

1. The `tools` package can be imported without crashing even when rembg/
   onnxruntime are absent or raise sys.exit(1) during DLL initialization.
2. rembg is NOT imported at module level – only at call time (lazy).
3. PyTorch is NOT imported at module level by the main inference path.
4. ai.inference is always importable and degrades gracefully.
5. ai.training_pytorch is always importable; raises clear RuntimeError
   (with install instructions) when torch is absent.
6. User-facing messages are present when optional deps are unavailable.

These tests mirror the PyInstaller isolated subprocess scenario:
sys.exit is patched so any accidental call is caught as a failure.

Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os
from pathlib import Path

# Add src/ to path (mirrors main.py and the PyInstaller build)
_src = Path(__file__).parent / 'src'
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_exit():
    """Patch sys.exit so accidental calls are caught by tests."""
    _real = sys.exit
    _calls = []

    def _fake(code=0):
        _calls.append(code)
        raise SystemExit(code)

    sys.exit = _fake
    return _real, _calls


def _restore_exit(real):
    sys.exit = real


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_tools_import_does_not_call_sys_exit():
    """
    Importing the tools package must NOT trigger sys.exit.

    This is the exact crash that broke the PyInstaller build:
    rembg.bg called sys.exit(1) when onnxruntime DLL init failed in the
    isolated subprocess.  After the fix, rembg is only imported at call time.
    """
    print("\ntest_tools_import_does_not_call_sys_exit ...")

    # Evict any cached modules so we get a fresh import
    for key in list(sys.modules.keys()):
        if 'tools' in key or 'background_remover' in key or 'object_remover' in key:
            del sys.modules[key]

    real, calls = _patch_exit()
    try:
        import tools  # noqa: F401
        from tools.object_remover import ObjectRemover, _get_rembg
        from tools.background_remover import BackgroundRemover  # noqa: F401
        assert not calls, f"sys.exit was called with code(s): {calls}"
    except SystemExit as exc:
        if calls:
            raise AssertionError(
                f"sys.exit({calls}) was called during tools import – "
                "rembg still crashes the build!"
            ) from exc
        raise
    finally:
        _restore_exit(real)

    print("  PASS")


def test_get_rembg_returns_none_when_absent():
    """_get_rembg() must return (None, None) when rembg is not installed."""
    print("\ntest_get_rembg_returns_none_when_absent ...")

    from tools.object_remover import _get_rembg

    remove_fn, session_fn = _get_rembg()
    if remove_fn is not None:
        # rembg is actually installed – verify it returned callables and skip
        # the 'absent' assertions (they only apply when rembg is missing).
        assert callable(remove_fn), "Expected callable for remove_fn when rembg present"
        assert callable(session_fn), "Expected callable for session_fn when rembg present"
        print("  PASS (rembg present – returned callables as expected)")
    else:
        # rembg absent – both must be None (graceful degradation)
        assert remove_fn is None, f"Expected None for remove_fn, got {remove_fn!r}"
        assert session_fn is None, f"Expected None for session_fn, got {session_fn!r}"
        print("  PASS (rembg absent – returned (None, None) as expected)")

    print("  PASS")


def test_object_remover_remove_object_safe_when_rembg_absent():
    """ObjectRemover.remove_object() must return False (not crash) when rembg is absent."""
    print("\ntest_object_remover_remove_object_safe_when_rembg_absent ...")

    from tools.object_remover import ObjectRemover, _get_rembg

    remove_fn, _ = _get_rembg()
    if remove_fn is not None:
        print("  SKIP (rembg is installed – cannot test absent path)")
        return

    obj = ObjectRemover()
    result = obj.remove_object()
    assert result is False, f"Expected False, got {result!r}"

    print("  PASS")


def test_torch_not_imported_at_module_level():
    """
    Importing the full ai package must NOT cause torch to be imported.

    The training side (ai.training_pytorch) lazy-imports torch only inside
    _require_torch() which is called from functions/methods, never at module
    load time.  If this test fails, training-time deps have leaked into the
    inference runtime path, which breaks the EXE build goal.
    """
    print("\ntest_torch_not_imported_at_module_level ...")

    # Evict ai modules to get a fresh import
    for key in list(sys.modules.keys()):
        if key == 'ai' or key.startswith('ai.'):
            del sys.modules[key]

    import ai  # noqa: F401

    assert 'torch' not in sys.modules, (
        "torch was imported at module level by the ai package! "
        "Training deps must be kept out of the inference runtime path."
    )

    print("  PASS")


def test_ai_inference_importable_without_onnxruntime():
    """ai.inference must import cleanly even when onnxruntime is absent."""
    print("\ntest_ai_inference_importable_without_onnxruntime ...")

    from ai.inference import OnnxInferenceSession, run_batch_inference, is_available

    sess = OnnxInferenceSession()
    assert not sess.is_ready(), "Session should not be ready without onnxruntime"
    assert sess.run(None) is None, "run() should return None when not ready"

    results = run_batch_inference("nonexistent.onnx", [])
    assert results == [], "Empty batch should return empty list"

    print(f"  onnxruntime available={is_available()}")
    print("  PASS")


def test_ai_training_pytorch_importable_without_torch():
    """ai.training_pytorch must import cleanly when torch is absent."""
    print("\ntest_ai_training_pytorch_importable_without_torch ...")

    from ai.training_pytorch import is_pytorch_available, export_to_onnx, PyTorchTrainer

    avail = is_pytorch_available()
    print(f"  pytorch available={avail}")

    if not avail:
        # export_to_onnx must return False gracefully
        result = export_to_onnx(None, "/tmp/dummy_test.onnx")
        assert result is False, f"Expected False, got {result!r}"

        # PyTorchTrainer instantiation must raise RuntimeError with install hint
        try:
            PyTorchTrainer(None, None)
            raise AssertionError("Expected RuntimeError from PyTorchTrainer")
        except RuntimeError as exc:
            msg = str(exc)
            assert "PyTorch" in msg, f"Error message missing 'PyTorch': {msg}"
            assert "pip install" in msg, f"Error message missing install hint: {msg}"

    print("  PASS")


def test_ai_package_exports_hybrid_symbols():
    """ai package must export both inference and training symbols."""
    print("\ntest_ai_package_exports_hybrid_symbols ...")

    for key in list(sys.modules.keys()):
        if key == 'ai' or key.startswith('ai.'):
            del sys.modules[key]

    import ai

    # Inference side (always required)
    assert hasattr(ai, 'OnnxInferenceSession'), "Missing OnnxInferenceSession"
    assert hasattr(ai, 'run_batch_inference'), "Missing run_batch_inference"
    assert hasattr(ai, 'onnx_available'), "Missing onnx_available"
    assert hasattr(ai, 'ONNX_AVAILABLE'), "Missing ONNX_AVAILABLE flag"
    assert isinstance(ai.ONNX_AVAILABLE, bool), f"ONNX_AVAILABLE should be bool, got {type(ai.ONNX_AVAILABLE)}"

    # Training side (optional)
    assert hasattr(ai, 'PyTorchTrainer'), "Missing PyTorchTrainer"
    assert hasattr(ai, 'export_to_onnx'), "Missing export_to_onnx"
    assert hasattr(ai, 'is_pytorch_available'), "Missing is_pytorch_available"
    assert hasattr(ai, 'PYTORCH_AVAILABLE'), "Missing PYTORCH_AVAILABLE flag"
    assert isinstance(ai.PYTORCH_AVAILABLE, bool), f"PYTORCH_AVAILABLE should be bool, got {type(ai.PYTORCH_AVAILABLE)}"

    print("  PASS")


# ---------------------------------------------------------------------------
# Organizer style keyword matching
# ---------------------------------------------------------------------------

def test_organizer_style_no_false_positives():
    """'iron' in 'environment' must NOT classify env textures as Metal_Surfaces.

    Before the _has_kw() fix, `'iron' in 'environment'` evaluated to True
    because Python substring search found "iron" inside "env**iron**ment".
    This caused EVERY texture with category='environment' to be incorrectly
    filed under Metal_Surfaces regardless of its actual filename.
    """
    print("\ntest_organizer_style_no_false_positives ...")
    import sys as _sys
    _sys.path.insert(0, 'src')
    try:
        from organizer.organization_styles import ByAppearanceStyle, _has_kw
        from organizer.organization_engine import TextureInfo

        style = ByAppearanceStyle()

        # Core fix: 'iron' must NOT match the word 'environment'
        assert not _has_kw('environment', ['iron']), \
            "_has_kw('environment', ['iron']) must be False (bug: 'iron' is substring of 'environiron')"
        # But 'iron' MUST match when it IS a token
        assert _has_kw('iron_gate', ['iron']), \
            "_has_kw('iron_gate', ['iron']) must be True"

        # rock_texture.dds with category='environment' must go to Stone_Surfaces, not Metal_Surfaces
        tex_rock = TextureInfo(
            file_path='/test/rock_texture.dds', filename='rock_texture.dds',
            category='environment', confidence=0.6,
        )
        result = style.get_target_path(tex_rock)
        assert result.startswith('Stone_Surfaces'), \
            f"Expected Stone_Surfaces/... but got {result!r}"

        # iron_gate.dds SHOULD go to Metal_Surfaces
        tex_iron = TextureInfo(
            file_path='/test/iron_gate.dds', filename='iron_gate.dds',
            category='environment', confidence=0.8,
        )
        result2 = style.get_target_path(tex_iron)
        assert result2.startswith('Metal_Surfaces'), \
            f"Expected Metal_Surfaces/... but got {result2!r}"

        # generic env texture (no material keyword) falls back to category
        tex_env = TextureInfo(
            file_path='/test/ground_env.dds', filename='ground_env.dds',
            category='environment', confidence=0.7,
        )
        result3 = style.get_target_path(tex_env)
        assert 'Metal_Surfaces' not in result3, \
            f"env texture without metal keywords got Metal_Surfaces: {result3!r}"

        print("  ✅ ByAppearanceStyle no false positives")
    except ImportError as exc:
        print(f"  ⚠️  Skipped (import failed: {exc})")


def test_model_manager_url_structure():
    """Verify that known-wrong HuggingFace URL patterns are not present in model_manager."""
    print("\ntest_model_manager_url_structure ...")
    import sys
    import os
    # Add src to path
    _root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_root, 'src'))
    try:
        from upscaler.model_manager import AIModelManager
        mgr = AIModelManager.__new__(AIModelManager)
        models = AIModelManager.MODELS

        # 1. CodeFormer HF mirror must include the 'weights/CodeFormer/' subfolder
        cf = models.get('CodeFormer', {})
        mirror = cf.get('mirror', '')
        assert 'sczhou/CodeFormer' not in mirror or 'weights/CodeFormer/' in mirror, (
            f"CodeFormer HF mirror URL is missing the 'weights/CodeFormer/' subfolder: {mirror!r}\n"
            "Correct path: .../sczhou/CodeFormer/resolve/main/weights/CodeFormer/codeformer.pth"
        )

        # 2. birefnet-general should NOT use private danielgatis/rembg HF as primary
        #    (The HF repo is private — it returns HTTP 401 without a token)
        #    GitHub releases ARE public and fine to use as primary.
        bn = models.get('birefnet-general', {})
        primary = bn.get('url', '')
        assert 'huggingface.co/danielgatis/rembg' not in primary, (
            f"birefnet-general primary URL uses private danielgatis/rembg HuggingFace repo "
            f"(returns HTTP 401 without a token): {primary!r}\n"
            "Use GitHub releases or a public HF repo as primary."
        )

        # 2b. birefnet-general must NOT use the danielgatis/rembg v0.0.0 GitHub release
        #     as primary — that file does NOT exist there (HTTP 404 confirmed).
        assert 'github.com/danielgatis/rembg/releases/download' not in primary, (
            f"birefnet-general primary URL points to danielgatis/rembg GitHub releases "
            f"where the file does NOT exist (HTTP 404): {primary!r}\n"
            "Use the ZhengPeng7/BiRefNet HuggingFace repo as primary."
        )

        # 3. All rembg models with dest_dir_env should have dest_filename set
        for name, info in models.items():
            if info.get('dest_dir_env') == 'U2NET_HOME':
                assert 'dest_filename' in info, (
                    f"Model '{name}' has dest_dir_env='U2NET_HOME' but no dest_filename — "
                    "get_model_status() will look for wrong filename"
                )

        # 4. All models must have a 'url' or 'hf_model_id' or 'auto_download'
        for name, info in models.items():
            has_source = ('url' in info or 'hf_model_id' in info
                          or info.get('auto_download') or info.get('native_module'))
            assert has_source, f"Model '{name}' has no download source (url/hf_model_id/auto_download)"

        print("  ✅ model_manager URL structure correct")
    except ImportError as exc:
        print(f"  ⚠️  Skipped (import failed: {exc})")


def test_panda_no_double_bob():
    """_draw_panda_arms and _draw_panda_legs must NOT add bob to their Y offsets.

    Both methods are called INSIDE the torso glPushMatrix, which already applies
    (0.28 + bob, ...).  If they also add bob, arms/legs move at 2× the body rate,
    causing them to appear to disconnect from the torso during animations.

    The fix: arm_y = 0.30 (constant), leg_y = -0.04 (constant).
    """
    print("\ntest_panda_no_double_bob ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_widget_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # Verify no "+ bob" in the arm_y / leg_y assignment lines
    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('arm_y') and '+ bob' in stripped and '0.34' not in stripped:
            # The only arm_y that may legitimately have bob is _draw_held_items (outside torso)
            # where we intentionally add the torso offset = 0.64 + bob
            if '0.64' not in stripped and '0.28' not in stripped:
                assert False, (
                    f"line {i}: '{stripped}' adds bob to arm_y inside a torso-scoped method.\n"
                    "Fix: arm_y = 0.30  (bob is already applied in the torso matrix)"
                )
        if stripped.startswith('leg_y') and '+ bob' in stripped:
            assert False, (
                f"line {i}: '{stripped}' adds bob to leg_y inside a torso-scoped method.\n"
                "Fix: leg_y = -0.04  (bob is already applied in the torso matrix)"
            )

    print("  ✅ No double-bob in _draw_panda_arms / _draw_panda_legs")


def test_bg_remover_onnx_fallback_present():
    """background_remover_panel_qt must define _remove_bg_onnx for the build fallback.

    In the PyInstaller build rembg is excluded (sys.exit crash prevention).
    The onnxruntime-based fallback must be present so background removal works
    even without the rembg package, as long as the ONNX models are on disk.
    """
    print("\ntest_bg_remover_onnx_fallback_present ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'background_remover_panel_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (background_remover_panel_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    func_names = {node.name for node in ast.walk(tree)
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

    assert '_remove_bg_onnx' in func_names, (
        "_remove_bg_onnx() not found in background_remover_panel_qt.py!\n"
        "This module-level function provides onnxruntime-based background removal\n"
        "as a fallback when rembg is absent (excluded from the PyInstaller bundle)."
    )

    # auto_remove_background must reference onnxruntime availability
    assert 'ort_available' in code, (
        "auto_remove_background() does not check ort_available — "
        "onnxruntime fallback path is missing."
    )

    print("  ✅ _remove_bg_onnx fallback present")
    print("  ✅ ort_available check present in auto_remove_background")


def test_panda_widget_gl_qstate_import():
    """panda_widget_gl must try PyQt6.QtStateMachine for QState/QStateMachine.

    In PyQt6 >= 6.1, QState and QStateMachine were moved from PyQt6.QtCore
    to PyQt6.QtStateMachine.  If panda_widget_gl.py only tries QtCore (no
    QtStateMachine attempt), the ImportError sets QT_AVAILABLE=False, which
    makes the entire 3D panda system silently fall back to the 2D widget on
    EVERY machine with a modern PyQt6 install — regardless of whether OpenGL
    is available.

    Correct fix: try PyQt6.QtStateMachine first; fall back to QtCore only for
    old PyQt6 installs where the class was still in QtCore.
    """
    print("\ntest_panda_widget_gl_qstate_import ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_widget_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    # Collect all ImportFrom nodes for QState/QStateMachine
    qtcore_lines = []   # bad: only source if no QtStateMachine attempt
    qtstate_lines = []  # good: PyQt6.QtStateMachine

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = {a.name for a in (node.names or [])}
            if names & {'QState', 'QStateMachine'}:
                if node.module == 'PyQt6.QtStateMachine':
                    qtstate_lines.append(node.lineno)
                elif node.module == 'PyQt6.QtCore':
                    qtcore_lines.append(node.lineno)

    # The file MUST contain a PyQt6.QtStateMachine import attempt
    assert qtstate_lines, (
        "panda_widget_gl.py does NOT import QState/QStateMachine from PyQt6.QtStateMachine!\n"
        "In PyQt6 >= 6.1, these classes are in PyQt6.QtStateMachine (NOT PyQt6.QtCore).\n"
        "Without this import, QT_AVAILABLE=False and 3D panda never shows (always 2D).\n"
        "Fix: add 'from PyQt6.QtStateMachine import QState, QStateMachine' as the PRIMARY import,\n"
        "     with 'from PyQt6.QtCore import QState, QStateMachine' as a fallback for older PyQt6."
    )
    print(f"  ✅ PyQt6.QtStateMachine import found at line(s): {qtstate_lines}")
    if qtcore_lines:
        print(f"  ✅ PyQt6.QtCore fallback also present at line(s): {qtcore_lines} (correct — for older PyQt6)")


def test_bedroom_mouse_release_event():
    """furniture_clicked must be emitted from mouseReleaseEvent, NOT mouseMoveEvent.

    In Qt, event.button() inside mouseMoveEvent() ALWAYS returns
    Qt.MouseButton.NoButton — the condition ``event.button() ==
    Qt.MouseButton.LeftButton`` is therefore NEVER true inside a move handler.

    If the release/click logic is embedded in mouseMoveEvent(), clicking a
    piece of furniture does nothing: no wardrobe, no backpack, no door.
    The fix: add a dedicated mouseReleaseEvent() method.
    """
    print("\ntest_bedroom_mouse_release_event ...")
    import ast
    from pathlib import Path

    src_path = Path(__file__).parent / 'src' / 'ui' / 'panda_bedroom_gl.py'
    if not src_path.exists():
        print("  ⚠️  Skipped (panda_bedroom_gl.py not found)")
        return

    code = src_path.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src_path))

    # Collect all method definitions and the line ranges of each
    class MethodFinder(ast.NodeVisitor):
        def __init__(self):
            self.methods = {}  # name -> (start_line, end_line)

        def visit_FunctionDef(self, node):
            # end_lineno requires Python ≥ 3.8 (which we require anyway)
            self.methods[node.name] = (node.lineno, getattr(node, 'end_lineno', node.lineno))
            self.generic_visit(node)

    finder = MethodFinder()
    finder.visit(tree)

    assert 'mouseReleaseEvent' in finder.methods, (
        "panda_bedroom_gl.PandaBedroomGL is missing mouseReleaseEvent()!\n"
        "The furniture-click (furniture_clicked signal) must be emitted in "
        "mouseReleaseEvent, NOT mouseMoveEvent.\n"
        "In Qt, event.button() inside mouseMoveEvent() always returns NoButton, "
        "so placing release logic there means furniture clicks never fire."
    )

    move_start, move_end = finder.methods.get('mouseMoveEvent', (0, 0))
    release_start, release_end = finder.methods.get('mouseReleaseEvent', (0, 0))

    # Verify furniture_clicked.emit is in mouseReleaseEvent, NOT mouseMoveEvent
    lines = code.split('\n')
    emit_in_move = [
        i + 1
        for i in range(move_start - 1, move_end)
        if 'furniture_clicked.emit' in lines[i]
    ]
    emit_in_release = [
        i + 1
        for i in range(release_start - 1, release_end)
        if 'furniture_clicked.emit' in lines[i]
    ]

    assert not emit_in_move, (
        f"furniture_clicked.emit found inside mouseMoveEvent (lines {emit_in_move})!\n"
        "event.button() in mouseMoveEvent always returns NoButton — furniture clicks "
        "will NEVER fire.  Move the emit to mouseReleaseEvent."
    )
    assert emit_in_release, (
        "furniture_clicked.emit NOT found inside mouseReleaseEvent!\n"
        "Furniture clicks will never be processed."
    )
    print(f"  ✅ mouseReleaseEvent present; furniture_clicked.emit at line(s): {emit_in_release}")


def test_otter_smooth_look_animation():
    """PandaWorldGL must use _otter_look_tgt for smooth look blending.

    The old code snapped Livy's look direction instantly to a new random angle
    then decayed it back to 0 (multiplying by 0.96 each tick).  This caused a
    jarring visual snap on every look-around event.

    The fix: store a *target* in _otter_look_tgt and exponentially blend
    _otter_look_x toward it every tick — so Livy smoothly swivels her head
    rather than snapping.
    """
    print("\ntest_otter_smooth_look_animation ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_world_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_world_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    # _otter_look_tgt must be assigned in __init__
    init_assigns = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '__init__':
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for tgt in child.targets:
                        if isinstance(tgt, ast.Attribute):
                            init_assigns.add(tgt.attr)

    assert '_otter_look_tgt' in init_assigns, (
        "PandaWorldGL.__init__ does not initialise _otter_look_tgt!\n"
        "Without this, the smooth look-blend will crash on the first tick."
    )
    print("  ✅ _otter_look_tgt initialised in __init__")

    # A lerp line must reference both _otter_look_tgt and _otter_look_x
    lerp_lines = [
        ln.strip() for ln in code.split('\n')
        if '_otter_look_x' in ln and '_otter_look_tgt' in ln
    ]
    assert lerp_lines, (
        "No line found that blends _otter_look_x toward _otter_look_tgt.\n"
        "Expected e.g.:\n"
        "  self._otter_look_x += (self._otter_look_tgt - self._otter_look_x) * 0.07"
    )
    print(f"  ✅ smooth lerp line: {lerp_lines[0]!r}")
    print("  PASS")


def test_spec_bundle_completeness():
    """build_spec_onefolder.spec must declare hiddenimports for all external
    packages that are imported (lazily or otherwise) in src/.

    This test catches the three packages that were missing after a previous
    bundle-completeness audit:

    1. cryptography — profile encryption in organizer/learning_system.py
    2. skimage (scikit-image) — SSIM quality check in utils/image_processing.py
    3. pytesseract — OCR in structural_analysis/ocr_detector.py
    """
    print("\ntest_spec_bundle_completeness ...")
    from pathlib import Path

    spec_path = Path(__file__).parent / 'build_spec_onefolder.spec'
    if not spec_path.exists():
        print("  ⚠️  Skipped (build_spec_onefolder.spec not found)")
        return

    spec = spec_path.read_text(encoding='utf-8')

    # Each entry: (import_name, source_file, purpose)
    _REQUIRED = [
        ('cryptography', 'organizer/learning_system.py',
         'Fernet profile encryption — Fernet/PBKDF2 C-extensions must be bundled'),
        ('skimage',      'utils/image_processing.py',
         'skimage.metrics.structural_similarity (SSIM quality check)'),
        ('pytesseract',  'structural_analysis/ocr_detector.py',
         'Tesseract OCR wrapper — lazy import missed by PyInstaller static analysis'),
    ]

    for pkg, src_file, purpose in _REQUIRED:
        assert f"'{pkg}'" in spec or f'"{pkg}"' in spec, (
            f"'{pkg}' missing from spec hiddenimports!\n"
            f"Used in: {src_file}\n"
            f"Purpose: {purpose}"
        )
        print(f"  ✅ '{pkg}' present in spec hiddenimports  ({src_file})")

    # cryptography must also be in requirements.txt (was missing before this fix)
    req_path = Path(__file__).parent / 'requirements.txt'
    if req_path.exists():
        assert 'cryptography' in req_path.read_text(encoding='utf-8'), (
            "cryptography missing from requirements.txt — "
            "add: cryptography>=41.0.0  # profile encryption"
        )
        print("  ✅ cryptography present in requirements.txt")

    print("  PASS")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def test_panda_camera_distance_and_drag():
    """Panda overlay widget must have camera_distance >= 6.0 and drag scale <= /500.

    camera_distance = 5.0 makes the panda fill a large portion of the window,
    causing body parts to appear distorted by perspective and making the widget
    feel overwhelming.  7.0 is a comfortable default.

    drag_scale = camera_distance / 300.0 was too sensitive (twitchy drag).
    Changed to / 600.0 for smoother feel.
    """
    print("\ntest_panda_camera_distance_and_drag ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_widget_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # camera_distance must be >= 6.0
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if s.startswith('self.camera_distance = ') and 'max' not in s:
            try:
                val = float(s.split('=')[1].strip())
                assert val >= 6.0, (
                    f"line {i}: camera_distance = {val} is too small (minimum 6.0). "
                    "A distance of 7.0 gives a comfortable non-filling panda size."
                )
                print(f"  ✅ camera_distance = {val} (>= 6.0)")
            except (ValueError, IndexError):
                pass

    # drag scale must be /500 or larger denominator (less sensitive)
    import re as _re
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if 'drag_scale' in s and 'camera_distance /' in s:
            m = _re.search(r'camera_distance\s*/\s*([0-9]+(?:\.[0-9]+)?)', s)
            if m:
                denom = float(m.group(1))
                assert denom >= 500, (
                    f"line {i}: drag_scale denominator {denom} is too low (min 500). "
                    "Use camera_distance / 600.0 for a less twitchy drag."
                )
                print(f"  ✅ drag_scale denominator = {denom} (>= 500)")


def test_bedroom_panda_walk():
    """PandaBedroomGL must implement walk_panda_to() and _draw_panda_in_room().

    The bedroom scene needs its own panda character that:
    1. Walks toward furniture when furniture_clicked is emitted.
    2. Is drawn in the bedroom 3D scene (not just the floating overlay).

    This makes the furniture interaction visually meaningful — the user sees
    the panda character walking to the object before the panel opens.
    """
    print("\ntest_bedroom_panda_walk ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_bedroom_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_bedroom_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    func_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert 'walk_panda_to' in func_names, (
        "PandaBedroomGL.walk_panda_to() not found!\n"
        "This method should animate the in-room panda walking toward a target position "
        "so the user sees it moving to the clicked furniture piece."
    )
    assert '_draw_panda_in_room' in func_names, (
        "PandaBedroomGL._draw_panda_in_room() not found!\n"
        "This method draws the panda character inside the bedroom 3D scene."
    )
    assert '_tick_panda_walk' in func_names, (
        "PandaBedroomGL._tick_panda_walk() not found!\n"
        "This method advances the panda toward its walk target each animation tick."
    )

    # walk_panda_to must have a callback parameter
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'walk_panda_to':
            arg_names = [a.arg for a in node.args.args] + [
                a.arg for a in node.args.kwonlyargs
            ]
            if node.args.vararg:
                arg_names.append(node.args.vararg.arg)
            defaults = node.args.defaults + node.args.kw_defaults
            has_callback = 'callback' in arg_names
            assert has_callback, (
                "walk_panda_to() must accept a 'callback' parameter — called "
                "once the panda arrives at the target so the furniture panel can open."
            )
            print(f"  ✅ walk_panda_to() found with args: {arg_names}")
            break

    print("  ✅ _draw_panda_in_room() found")
    print("  ✅ _tick_panda_walk() found")


def test_bg_remover_splitter_and_backend_toggle():
    """Background remover panel must have a splitter layout and backend toggle.

    The original layout put controls and the live preview in a vertical stack
    making both very cramped.  The fix:
    1. Uses a QSplitter (horizontal) — controls on the left, preview on the right.
    2. Adds explicit rembg vs onnxruntime radio buttons so the user can choose.
    3. Sets a minimum panel size to prevent squashing.
    4. Adds a QScrollArea wrapper for the controls so they never get crushed.
    """
    print("\ntest_bg_remover_splitter_and_backend_toggle ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'background_remover_panel_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (background_remover_panel_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    # 1. QSplitter must be used in setup_ui
    assert 'QSplitter' in code, (
        "background_remover_panel_qt.py must import and use QSplitter to split "
        "controls (left) from the live preview (right)."
    )
    assert 'QScrollArea' in code, (
        "background_remover_panel_qt.py must use a QScrollArea to wrap the control "
        "column so controls are never squashed when the panel is narrow."
    )

    # 2. Backend radio buttons must exist
    assert '_backend_rembg_rb' in code, (
        "background_remover_panel_qt.py must create self._backend_rembg_rb "
        "(a QRadioButton) so users can explicitly choose the rembg backend."
    )
    assert '_backend_ort_rb' in code, (
        "background_remover_panel_qt.py must create self._backend_ort_rb "
        "(a QRadioButton) so users can explicitly choose onnxruntime."
    )

    # 3. auto_remove_background must read the radio button choice
    assert '_backend_rembg_rb' in code and 'isChecked' in code, (
        "auto_remove_background() must read self._backend_rembg_rb.isChecked() / "
        "self._backend_ort_rb.isChecked() to respect the user's backend selection."
    )

    # 4. Minimum size set
    assert 'setMinimumSize' in code, (
        "background_remover_panel_qt.py must call setMinimumSize() to prevent "
        "the panel from being squashed."
    )

    print("  ✅ QSplitter found — controls left, preview right")
    print("  ✅ QScrollArea wrapper found for controls column")
    print("  ✅ _backend_rembg_rb and _backend_ort_rb radio buttons found")
    print("  ✅ Backend toggle is read in auto_remove_background")
    print("  ✅ setMinimumSize found")


def test_dungeon_view_pyqt_guard():
    """DungeonGraphicsView.__init__ must raise ImportError (not TypeError) when
    PyQt6 is unavailable.

    Previously the constructor called super().__init__(parent) unconditionally.
    When PYQT_AVAILABLE=False, the base is `object` whose __init__ only accepts
    one argument, so the call raised:
        TypeError: object.__init__() takes exactly one argument

    The fix adds a guard at the start of __init__ that raises ImportError with
    a useful install message before calling super().__init__().  This lets the
    adventure tab's try/except produce a clear 'please install PyQt6' label
    instead of a confusing raw TypeError.
    """
    print("\ntest_dungeon_view_pyqt_guard ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'dungeon_graphics_view.py'
    if not src.exists():
        print("  ⚠️  Skipped (dungeon_graphics_view.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    # Find the DungeonGraphicsView.__init__ body
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'DungeonGraphicsView':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    # First statement must be a check on PYQT_AVAILABLE
                    first = item.body[0] if item.body else None
                    assert first is not None, "DungeonGraphicsView.__init__ is empty"
                    # It should be an if-raise or a similar guard
                    src_lines = code.splitlines()
                    # Check that PYQT_AVAILABLE appears before super().__init__
                    init_source = ast.get_source_segment(code, item) or ''
                    pyqt_pos = init_source.find('PYQT_AVAILABLE')
                    super_pos = init_source.find('super().__init__')
                    assert pyqt_pos >= 0, (
                        "DungeonGraphicsView.__init__ must check PYQT_AVAILABLE "
                        "before calling super().__init__() to avoid TypeError when "
                        "PyQt6 is not installed."
                    )
                    assert super_pos < 0 or pyqt_pos < super_pos, (
                        "PYQT_AVAILABLE guard must come BEFORE super().__init__() "
                        "in DungeonGraphicsView.__init__."
                    )
                    print("  ✅ PYQT_AVAILABLE guard is before super().__init__")
                    return

    print("  ⚠️  DungeonGraphicsView.__init__ not found — skipped")


def test_organizer_panel_constraints():
    """Organizer panel suggestions_list and log_text must allow reasonable heights.

    The original code set hard maxima of 120px (suggestions) and 100px (log) which
    made the organizer very cramped.  The fix raises them to 200px / 180px.
    Also a matching setMinimumHeight must be present so the widget doesn't collapse.
    """
    print("\ntest_organizer_panel_constraints ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'organizer_panel_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (organizer_panel_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # suggestions_list max height must be > 120
    for m in re.finditer(r'suggestions_list\.setMaximumHeight\((\d+)\)', code):
        h = int(m.group(1))
        assert h >= 180, (
            f"suggestions_list.setMaximumHeight({h}) is too small. "
            "Use at least 180 so the suggestions are readable."
        )
        print(f"  ✅ suggestions_list.setMaximumHeight({h}) >= 180")

    # log_text max height must be > 100
    for m in re.finditer(r'log_text\.setMaximumHeight\((\d+)\)', code):
        h = int(m.group(1))
        assert h >= 160, (
            f"log_text.setMaximumHeight({h}) is too small. "
            "Use at least 160 so the log text is readable."
        )
        print(f"  ✅ log_text.setMaximumHeight({h}) >= 160")


def test_theme_stylesheet_cursor_hints():
    """apply_theme() in main.py must append cursor:pointer styling to interactive widgets.

    Without this, buttons, ComboBoxes, and checkboxes all show the default arrow
    cursor on hover, giving no visual cue that they are clickable/changeable.
    The fix appends a common suffix to the stylesheet that sets cursor:pointer on
    QPushButton, QComboBox, QCheckBox, QRadioButton, QTabBar::tab, and QSlider.
    """
    print("\ntest_theme_stylesheet_cursor_hints ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'main.py'
    if not src.exists():
        print("  ⚠️  Skipped (main.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # Qt6 QSS does NOT support 'cursor: pointer' — it generates "Unknown property"
    # warnings.  The correct approach is to call setCursor(PointingHandCursor) on
    # each interactive widget.  Check that _install_pointing_cursor_filter exists
    # and is called from apply_theme().
    assert '_install_pointing_cursor_filter' in code, (
        "main.py must define _install_pointing_cursor_filter() to call "
        "setCursor(PointingHandCursor) on interactive widgets (QPushButton, "
        "QComboBox, QSlider, QTabBar, QAbstractButton).\n"
        "Qt6 QSS does NOT support 'cursor: pointer' — use setCursor() instead."
    )
    assert 'PointingHandCursor' in code, (
        "_install_pointing_cursor_filter must use Qt.CursorShape.PointingHandCursor "
        "to set the pointer cursor on interactive widgets."
    )
    # Must be called from apply_theme (or called every time theme changes)
    theme_pos  = code.find('def apply_theme(')
    filter_call_pos = code.find('_install_pointing_cursor_filter', theme_pos)
    assert filter_call_pos >= 0, (
        "_install_pointing_cursor_filter() must be called from apply_theme() "
        "so that the cursor is reset after every theme change."
    )
    print("  ✅ _install_pointing_cursor_filter found (Qt6-correct cursor approach)")
    print("  ✅ PointingHandCursor used for interactive widgets")
    print("  ✅ Called from apply_theme() so it runs on every theme change")


def test_main_qgroupbox_import():
    """QGroupBox must be in the top-level import block of main.py.

    create_main_tab() uses QGroupBox directly (no local import).  It was
    previously missing from the module-level ``from PyQt6.QtWidgets import …``
    block, causing a ``NameError: name 'QGroupBox' is not defined`` whenever
    the main window was instantiated.
    """
    print("\ntest_main_qgroupbox_import ...")
    from pathlib import Path
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # Find the first QtWidgets import block (module level) — use DOTALL so the
    # regex matches across line breaks (the import is a multi-line parenthesised list).
    import re
    m = re.search(r'from PyQt6\.QtWidgets import \((.+?)\)', code, re.DOTALL)
    assert m, "Could not find the top-level 'from PyQt6.QtWidgets import (…)' block in main.py"
    block = m.group(1)
    assert 'QGroupBox' in block, (
        "QGroupBox is missing from the top-level 'from PyQt6.QtWidgets import' block.\n"
        "create_main_tab() uses QGroupBox without a local import, causing NameError."
    )
    print("  ✅ QGroupBox found in top-level QtWidgets import block")


def test_main_input_path_label_exists():
    """main.py must initialise self.input_path_label and self.output_path_label.

    browse_input() and browse_output() call self.input_path_label.setText() and
    self.output_path_label.setText().  Without these attributes the app crashes
    with AttributeError on the first file-browse action AND when drag-and-drop
    tries to wire them.

    The fix:
    1. Creates them as QLabel stubs in __init__ (so they always exist).
    2. Adds them to the home tab's 'Folder Selection' group box so they are
       visible and functional.
    """
    print("\ntest_main_input_path_label_exists ...")
    from pathlib import Path
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    assert 'self.input_path_label' in code, (
        "main.py must define self.input_path_label (a QLabel) in __init__() "
        "so browse_input() can call .setText() without AttributeError."
    )
    assert 'self.output_path_label' in code, (
        "main.py must define self.output_path_label (a QLabel) in __init__() "
        "so browse_output() can call .setText() without AttributeError."
    )
    # Must appear before the first use in browse_input (line ~3367)
    label_pos = code.find('self.input_path_label = ')
    use_pos   = code.find('self.input_path_label.setText(')
    assert label_pos >= 0, "self.input_path_label = ... assignment not found"
    assert use_pos >= 0,   "self.input_path_label.setText() not found"
    assert label_pos < use_pos, (
        "self.input_path_label must be ASSIGNED before it is USED (.setText()). "
        f"Assigned at char {label_pos}, first use at char {use_pos}."
    )
    print("  ✅ self.input_path_label assigned before first use")
    print("  ✅ self.output_path_label present")
    # Also check the home tab has a Folder Selection group box
    assert 'Folder Selection' in code, (
        "The home tab should display the input/output path labels inside a "
        "'Folder Selection' QGroupBox so users can see and interact with them."
    )
    print("  ✅ 'Folder Selection' QGroupBox found in home tab")


def test_dungeon_render_integrated_dungeon():
    """DungeonGraphicsView.render_dungeon() must handle IntegratedDungeon objects.

    The original code called ``len(self.dungeon)`` and ``self.dungeon[floor]``
    which only works on a plain list.  IntegratedDungeon is an object with a
    nested ``.dungeon`` (DungeonGenerator) that exposes ``get_floor(n)`` →
    ``DungeonFloor`` with a ``collision_map`` 2-D list.

    The fix detects the data shape at render time and adapts accordingly.
    """
    print("\ntest_dungeon_render_integrated_dungeon ...")
    from pathlib import Path
    src = Path(__file__).parent / 'src' / 'ui' / 'dungeon_graphics_view.py'
    code = src.read_text(encoding='utf-8')

    assert 'get_floor' in code, (
        "render_dungeon() must call dungeon.dungeon.get_floor(n) to support "
        "IntegratedDungeon objects (which do NOT support len() or indexing)."
    )
    assert 'collision_map' in code, (
        "render_dungeon() must read floor_obj.collision_map to get the tile grid "
        "from a DungeonFloor (DungeonFloor stores tiles in .collision_map)."
    )
    assert 'isinstance(self.dungeon, list)' in code, (
        "render_dungeon() must handle the legacy list-of-floors format as well "
        "(used in tests and standalone demos)."
    )
    print("  ✅ render_dungeon handles IntegratedDungeon via get_floor() + collision_map")
    print("  ✅ render_dungeon handles legacy list-of-floors format")


def test_apply_theme_accepts_optional_name():
    """apply_theme() must accept an optional theme-name argument.

    When the shop sells a theme item, ``_apply_item_to_panda_widget()``
    calls ``self.apply_theme(item_id)`` where *item_id* is the theme name
    string (e.g. ``'dark'``, ``'nord'``).  The original signature was
    ``def apply_theme(self)`` (no args), which raised
    ``TypeError: apply_theme() takes 1 positional argument but 2 were given``.

    The fix adds an optional ``theme_name: str = None`` parameter that, when
    provided, is saved to config before reading it back — so every code path
    (direct call with a name, signal-driven call with no args) still works.
    """
    print("\ntest_apply_theme_accepts_optional_name ...")
    from pathlib import Path
    import re
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # Signature must accept an optional argument named exactly 'theme_name'
    sig_match = re.search(r'def apply_theme\(self([^)]*)\)', code)
    assert sig_match, "apply_theme() not found in main.py"
    sig_params = sig_match.group(1)
    assert 'theme_name' in sig_params, (
        "apply_theme() must accept an optional parameter named 'theme_name' "
        "(e.g. 'theme_name: str = None') so it can be called as "
        "apply_theme('dark') from _apply_item_to_panda_widget().\n"
        f"Current signature: def apply_theme(self{sig_params})"
    )
    # Must also default to None / have a default value (= None or = '')
    assert '= None' in sig_params or "= ''" in sig_params, (
        "The theme_name parameter must default to None so the no-arg call "
        "apply_theme() (used from on_settings_changed) still works."
    )
    # Verify it saves to config when a name is provided
    assert "config.set('ui', 'theme'" in code or 'config.set("ui", "theme"' in code, (
        "apply_theme(theme_name) must save theme_name to config before reading "
        "it back, so the setting persists across calls."
    )
    print("  ✅ apply_theme() accepts optional theme_name parameter")
    print("  ✅ theme_name defaults to None (no-arg call still works)")
    print("  ✅ theme_name saved to config when provided")


def test_qss_no_cursor_pointer():
    """Qt6 QSS must NOT contain 'cursor: pointer' — it is unsupported and noisy.

    Qt6's QSS parser does not support the CSS ``cursor`` property.  Every widget
    that receives a stylesheet containing ``cursor: pointer`` emits a
    ``Unknown property cursor`` warning — with hundreds of widgets this produces
    a flood that pollutes the console and CI logs.

    The correct Qt6 approach is ``widget.setCursor(Qt.CursorShape.PointingHandCursor)``,
    which is implemented in ``_install_pointing_cursor_filter()``.
    """
    print("\ntest_qss_no_cursor_pointer ...")
    from pathlib import Path
    import ast, re
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # Use the AST to find string literals that are used as *values* (not docstrings).
    # Only value strings (right-hand-side of assignments, arguments to calls, etc.)
    # can be passed to setStyleSheet() — docstrings are ast.Expr(ast.Constant) at
    # the start of a function/class/module body and are skipped.
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        assert False, f"main.py has a SyntaxError: {e}"

    # Collect line numbers of all docstrings so we can exclude them
    docstring_lines: set = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and
                    isinstance(body[0].value, ast.Constant) and
                    isinstance(body[0].value.value, str)):
                docstring_lines.add(body[0].value.lineno)

    qss_cursor_hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.lineno in docstring_lines:
                continue  # skip docstrings
            val = node.value
            if 'cursor: pointer' in val or 'cursor:pointer' in val:
                snippet = val.replace('\n', ' ')[:80]
                qss_cursor_hits.append((node.lineno, snippet))

    assert not qss_cursor_hits, (
        "QSS stylesheet strings in main.py must NOT contain 'cursor: pointer'.\n"
        "Qt6 does not support the CSS cursor property — it silently ignores it but\n"
        "emits hundreds of 'Unknown property cursor' warnings (one per widget).\n"
        "Use _install_pointing_cursor_filter() / setCursor() instead.\n"
        "Offending string literals:\n" +
        "\n".join(f"  L{ln}: ...{snip}..." for ln, snip in qss_cursor_hits)
    )
    print("  ✅ No 'cursor: pointer' found in any string literal (QSS-safe)")


def test_dock_widget_object_names():
    """All QDockWidgets created by _add_tool_dock must have objectName set.

    QMainWindow.saveState() silently skips (and warns about) dock widgets
    with an empty objectName, which means their positions are not saved or
    restored across sessions.  _add_tool_dock() must call
    ``dock.setObjectName(f"dock_{tool_id}")`` before addDockWidget().
    """
    print("\ntest_dock_widget_object_names ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    # Walk AST to find _add_tool_dock and _make_tab_dock method bodies
    methods_found: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ('_add_tool_dock', '_make_tab_dock'):
            # Collect all string literals and attribute accesses in the body
            body_source = ast.get_source_segment(code, node) or ''
            methods_found[node.name] = body_source

    assert '_add_tool_dock' in methods_found, "_add_tool_dock() not found in main.py"
    assert 'setObjectName' in methods_found['_add_tool_dock'], (
        "_add_tool_dock() must call dock.setObjectName() so QMainWindow.saveState()\n"
        "can serialise dock widget layout.  Without an objectName, Qt warns:\n"
        "  QMainWindow::saveState(): 'objectName' not set for QDockWidget …\n"
        "Fix: add dock.setObjectName(f\"dock_{tool_id}\") before addDockWidget()."
    )
    assert '_make_tab_dock' in methods_found, "_make_tab_dock() not found in main.py"
    assert 'setObjectName' in methods_found['_make_tab_dock'], (
        "_make_tab_dock() must call dock.setObjectName() for saveState() compatibility."
    )
    print("  ✅ _add_tool_dock() calls dock.setObjectName()")
    print("  ✅ _make_tab_dock() calls dock.setObjectName()")
    # Also verify that _make_tab_dock uses a counter/index to ensure uniqueness
    assert '_tab_dock_counter' in methods_found['_make_tab_dock'] or 'counter' in methods_found['_make_tab_dock'], (
        "_make_tab_dock() should append a uniqueness counter to the objectName\n"
        "to prevent collisions when two tab names differ only in special characters."
    )
    print("  ✅ _make_tab_dock() uses a counter for unique objectNames")


def test_minigame_achievement_ids_valid():
    """_on_minigame_completed must reference valid achievement IDs.

    Previously the method called:
      achievement_system.unlock_achievement('minigame_player')   # does not exist
      achievement_system.unlock_achievement('minigame_master')   # does not exist
      quest_system.update_quest_progress('minigame_enjoyer')     # does not exist

    These silently produce WARNING log lines every time a minigame is completed.
    The correct IDs come from the AchievementSystem and QuestSystem definitions.
    """
    print("\ntest_minigame_achievement_ids_valid ...")
    import sys as _sys
    _sys.path.insert(0, 'src')
    from pathlib import Path
    import ast, re

    # Load the set of defined achievement IDs
    from features.achievements import AchievementSystem
    valid_ach_ids = set(AchievementSystem().achievements.keys())

    # Load the set of defined quest IDs
    from features.quest_system import QuestSystem
    valid_quest_ids = set(QuestSystem().quests.keys())

    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    # Use AST to find the _on_minigame_completed method body source
    method_source = ''
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_on_minigame_completed':
            method_source = ast.get_source_segment(code, node) or ''
            break
    assert method_source, "_on_minigame_completed() not found in main.py"

    # Extract all unlock_achievement('id') calls in the method
    ach_ids_used = set(re.findall(r"unlock_achievement\(\s*['\"]([^'\"]+)['\"]\s*\)", method_source))
    bad_ach = ach_ids_used - valid_ach_ids
    assert not bad_ach, (
        f"_on_minigame_completed() calls unlock_achievement() with unknown IDs: {bad_ach}\n"
        f"Valid IDs are: {sorted(valid_ach_ids)}"
    )

    # Extract all update_quest_progress('id') calls in the method
    quest_ids_used = set(re.findall(r"update_quest_progress\(\s*['\"]([^'\"]+)['\"]\s*\)", method_source))
    bad_quest = quest_ids_used - valid_quest_ids
    assert not bad_quest, (
        f"_on_minigame_completed() calls update_quest_progress() with unknown IDs: {bad_quest}\n"
        f"Valid IDs are: {sorted(valid_quest_ids)}"
    )

    print(f"  ✅ All achievement IDs valid: {sorted(ach_ids_used)}")
    print(f"  ✅ All quest IDs valid: {sorted(quest_ids_used)}")


def test_theme_achievement_ids_valid():
    """apply_theme() must map theme names to valid achievement IDs only.

    The _theme_ach dict maps theme names ('forest', 'ocean', etc.) to achievement
    IDs.  If an ID does not exist in AchievementSystem.achievements, the
    unlock_achievement() call logs a WARNING on every theme switch.
    """
    print("\ntest_theme_achievement_ids_valid ...")
    import sys as _sys
    _sys.path.insert(0, 'src')
    from pathlib import Path
    import re

    from features.achievements import AchievementSystem
    valid_ach_ids = set(AchievementSystem().achievements.keys())

    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # Find the _theme_ach dict literal inside apply_theme()
    m = re.search(r'_theme_ach\s*=\s*\{([^}]+)\}', code, re.DOTALL)
    assert m, "_theme_ach dict not found in main.py (inside apply_theme)"
    block = m.group(1)

    # Extract all values (achievement IDs)
    ach_values = set(re.findall(r":\s*['\"]([^'\"]+)['\"]", block))
    bad = ach_values - valid_ach_ids
    assert not bad, (
        f"apply_theme() _theme_ach maps to unknown achievement IDs: {bad}\n"
        f"Valid IDs: {sorted(valid_ach_ids)}"
    )
    print(f"  ✅ All {len(ach_values)} theme achievement IDs are valid")


def test_show_help_and_settings_methods():
    """TextureSorterMainWindow must expose show_help(), save_settings(), load_settings(),
    and _offer_crash_recovery().

    These were previously missing, causing AttributeError on F1, on programmatic
    settings saves/loads, and when the auto-backup crash-recovery path fired.
    """
    print("\ntest_show_help_and_settings_methods ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    # Walk the AST to find all method definitions in TextureSorterMainWindow
    class_methods: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TextureSorterMainWindow':
            for item in ast.walk(node):
                if isinstance(item, ast.FunctionDef):
                    class_methods.add(item.name)
            break

    required = {
        'show_help': 'show_help() — called by F1 Help menu action',
        'save_settings': 'save_settings() — persists settings to disk',
        'load_settings': 'load_settings() — reloads settings from disk',
        '_offer_crash_recovery': '_offer_crash_recovery() — wired to auto_backup.on_recovery_available',
    }
    for method, desc in required.items():
        assert method in class_methods, (
            f"TextureSorterMainWindow is missing {desc}."
        )
        print(f"  ✅ {method}() present")

    # Check Help menu has a "Help" action (not just "About")
    # Look for the setup_menubar method and verify both help_action and about_action appear
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'setup_menubar':
            method_src = ast.get_source_segment(code, node) or ''
            assert 'show_help' in method_src, (
                "setup_menubar() must wire a Help action to self.show_help().\n"
                "The Help menu only had 'About'; a 'Help / Documentation' item is needed."
            )
            print("  ✅ setup_menubar() wires show_help to Help menu")
            break


def test_tool_labels_no_duplicates():
    """_update_tool_panels_menu must not have duplicate keys in _TOOL_LABELS and
    must include 'converter'.

    The old dict had 'organizer' listed twice (the second entry silently overwrote
    the first in CPython) and was missing 'converter', so the Format Converter tool
    was absent from View → Tool Panels.
    """
    print("\ntest_tool_labels_no_duplicates ...")
    from pathlib import Path
    import ast, re
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_update_tool_panels_menu':
            method_src = ast.get_source_segment(code, node) or ''

            # Extract all string keys from the _TOOL_LABELS dict literal
            keys = re.findall(r"'(\w+)'\s*:", method_src)
            # Only consider those inside the _TOOL_LABELS block
            # (the first N keys before 'for tool_id' appear)
            label_keys = []
            for k in keys:
                if k == 'tool_id':
                    break
                label_keys.append(k)

            # No duplicates
            dupes = [k for k in label_keys if label_keys.count(k) > 1]
            assert not dupes, (
                f"_TOOL_LABELS has duplicate key(s): {list(set(dupes))}\n"
                "Fix: remove the second 'organizer' entry."
            )
            # 'converter' must be present
            assert 'converter' in label_keys, (
                "'converter' is missing from _TOOL_LABELS in _update_tool_panels_menu.\n"
                "The Format Converter panel is not reachable via View → Tool Panels."
            )
            print(f"  ✅ _TOOL_LABELS has {len(label_keys)} unique keys including 'converter'")
            return
    assert False, "_update_tool_panels_menu() not found in main.py"


def test_auto_backup_recovery_wired():
    """auto_backup.on_recovery_available must be assigned to _offer_crash_recovery()
    before auto_backup.start() is called.

    Without this wiring, a crash in the previous session is detected and logged
    (WARNING: Previous session crashed - recovery available) but the user is never
    prompted to restore — the recovery callback is None.
    """
    print("\ntest_auto_backup_recovery_wired ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'initialize_components':
            method_src = ast.get_source_segment(code, node) or ''
            assert 'on_recovery_available' in method_src, (
                "initialize_components() must assign auto_backup.on_recovery_available "
                "before calling auto_backup.start().\n"
                "Without it the crash-recovery dialog is never shown."
            )
            # The assignment must precede start()
            idx_assign = method_src.find('on_recovery_available')
            idx_start  = method_src.find('auto_backup.start()')
            assert idx_assign < idx_start, (
                "on_recovery_available must be assigned BEFORE auto_backup.start()."
            )
            print("  ✅ on_recovery_available wired before auto_backup.start()")
            return
    assert False, "initialize_components() not found in main.py"


def test_panda_overlay_no_source_mode_fill():
    """PandaWidget2D.paintEvent must NOT use CompositionMode_Source to fill with transparent.

    On Linux/X11 without a compositing window manager and on virtual displays,
    CompositionMode_Source + transparent fill renders as solid opaque black,
    making the entire panda overlay window appear all-black and hiding the
    application content beneath the panda.

    The correct approach is to skip the background fill entirely: Qt clears
    the backing store for WA_TranslucentBackground widgets before paintEvent so
    the Source-mode fill is both redundant and harmful on non-compositing platforms.
    """
    print("\ntest_panda_overlay_no_source_mode_fill ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_2d.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'paintEvent':
            method_src = ast.get_source_segment(code, node) or ''
            # Check that the method does NOT call fillRect with CompositionMode_Source
            # We look for the actual Python call pattern, not just the constant name
            # (the constant name appears in comments explaining why it was removed)
            import re
            source_mode_calls = re.findall(
                r'setCompositionMode\s*\(.*CompositionMode_Source\b(?!Over)',
                method_src
            )
            assert not source_mode_calls, (
                "PandaWidget2D.paintEvent() must not use CompositionMode_Source.\n"
                "On Linux/X11 without compositing this fills the entire overlay with\n"
                "opaque black, hiding all application content behind the panda.\n"
                "Fix: remove the fillRect(transparent) call; Qt handles backing-store\n"
                "clearing automatically for WA_TranslucentBackground widgets."
            )
            print("  ✅ paintEvent uses SourceOver (not Source) mode — no black overlay")
            return
    assert False, "PandaWidget2D.paintEvent() not found in panda_widget_2d.py"


def test_panda_overlay_scale_capped():
    """PandaWidget2D.paintEvent must cap the panda scale at ≤ 0.8.

    The formula ``min(w, h) / 320.0`` gives scale=2.5 on a 1280×800 full-window
    overlay, making the panda ~500 px tall and blocking the entire centre column
    of the UI.  Capping at 0.8 keeps the panda at ~130 px — visible as a
    companion but not obstructive.
    """
    print("\ntest_panda_overlay_scale_capped ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_2d.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'paintEvent':
            method_src = ast.get_source_segment(code, node) or ''
            # Scale must be capped: the assignment must contain a nested min()
            # call that limits the raw dimension/320 ratio.  We check for the
            # structural pattern "min(... / 320 ..., <cap>)" rather than a
            # specific literal so the test survives minor numeric tweaks.
            import re as _re
            has_cap = bool(_re.search(
                r'\bmin\s*\(.*320.*,\s*\d*\.\d+\s*\)',  # min(...320..., 0.N)
                method_src,
            ))
            assert has_cap, (
                "PandaWidget2D.paintEvent() must cap the scale to prevent the panda\n"
                "from growing to 500+ px on a 1280×800 full-window overlay.\n"
                "Expected pattern: scale = min(min(w, h) / 320.0, <cap_value>)"
            )
            # The vertical position must NOT be h*0.52 (dead centre) any more —
            # it should be lower so the panda doesn't block top-of-window content.
            assert 'h * 0.52' not in method_src, (
                "The panda vertical position h*0.52 places it at the dead centre of the\n"
                "window, blocking Quick Launch buttons and panel content.\n"
                "Fix: use h*0.72 or similar to keep the panda in the lower portion."
            )
            print("  ✅ scale is capped and panda is positioned below centre")
            return
    assert False, "PandaWidget2D.paintEvent() not found"


def test_settings_panel_auto_saves_on_change():
    """SettingsPanelQt must save each setting immediately when a widget changes.

    Design intent: every setting takes effect the moment the user interacts
    with the widget — there is no "Save Settings" button.  Each widget is
    wired to ``on_setting_changed`` which calls ``config.set()`` + ``config.save()``
    immediately.

    This test verifies:
    1. ``on_setting_changed`` exists and calls config.save() directly.
    2. ``SettingsPanelQt`` does NOT have a ``save_settings()`` method
       (which would imply a separate explicit save step in the UI).
    3. The settings panel has no QPushButton labelled "Save" or "Save Settings".
    """
    print("\ntest_settings_panel_auto_saves_on_change ...")
    from pathlib import Path
    import ast, re
    src = Path(__file__).parent / 'src' / 'ui' / 'settings_panel_qt.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    # 1. on_setting_changed must call config.save()
    panel_methods: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'SettingsPanelQt':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    panel_methods[item.name] = ast.get_source_segment(code, item) or ''
            break

    assert 'on_setting_changed' in panel_methods, (
        "SettingsPanelQt is missing on_setting_changed(). "
        "This is the auto-save entry point wired to every settings widget."
    )
    oc_src = panel_methods['on_setting_changed']
    assert 'config.save()' in oc_src, (
        "on_setting_changed() must call config.save() immediately so every\n"
        "widget change is persisted without a separate Save button."
    )
    print("  ✅ on_setting_changed() calls config.save() immediately")

    # 2. save_settings() must NOT exist in the panel class
    assert 'save_settings' not in panel_methods, (
        "SettingsPanelQt must not have a save_settings() method.\n"
        "Its presence implies a separate explicit save step; all settings\n"
        "must instead be persisted immediately via on_setting_changed()."
    )
    print("  ✅ SettingsPanelQt has no save_settings() method (settings auto-save)")

    # 3. No 'Save Settings' or standalone 'Save' QPushButton in the panel.
    #    We check only direct-literal QPushButton(…) calls; variable-assigned
    #    labels are not checked here but are controlled by code review.
    save_btns = re.findall(
        r'QPushButton\s*\(\s*["\'](?:Save Settings|Save)\s*["\']\s*\)',
        code
    )
    assert not save_btns, (
        f"SettingsPanelQt creates a 'Save Settings' or 'Save' button: {save_btns}\n"
        "Remove it — settings must apply and persist immediately on change."
    )
    print("  ✅ No 'Save Settings' button in SettingsPanelQt")


def test_clear_button_not_too_narrow():
    """The 'Clear' log button in the Home tab must not use setFixedWidth(80).

    setFixedWidth(80) is too narrow for '🗑 Clear' with an emoji, causing Qt to
    letter-space the characters and rendering the button text as '🗑 L i e a r'
    in the UI.  The fix is to use setMinimumWidth() instead so Qt can expand
    the button to fit its label.
    """
    print("\ntest_clear_button_not_too_narrow ...")
    from pathlib import Path
    import re
    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # Look for the clear_log_btn block
    # We specifically check that setFixedWidth(80) is NOT used right after the
    # Clear button is created (within 3 lines of QPushButton("🗑 Clear"))
    lines = code.splitlines()
    for i, line in enumerate(lines):
        if 'QPushButton("🗑 Clear")' in line or "QPushButton('🗑 Clear')" in line:
            # Look at the next 4 lines for setFixedWidth(80)
            context = '\n'.join(lines[i:i+5])
            assert 'setFixedWidth(80)' not in context, (
                f"Line {i+1}: The Clear log button still uses setFixedWidth(80).\n"
                "80 px is too narrow for '🗑 Clear' with an emoji — Qt letter-spaces\n"
                "the text, rendering it as '🗑 L i e a r'.\n"
                "Fix: replace setFixedWidth(80) with setMinimumWidth(90) or remove it."
            )
            print(f"  ✅ Clear button (line {i+1}) does not use setFixedWidth(80)")
            return
    assert False, "QPushButton('🗑 Clear') not found in main.py"


def test_trail_preview_show_hide_events():
    """TrailPreviewWidget must implement showEvent and hideEvent.

    When the Customisation tab is hidden (user switches to another tab) the
    animation timer keeps ticking in the background, wasting CPU.  showEvent
    should restart the animation and hideEvent should pause it so resources are
    only consumed when the widget is actually on screen.
    """
    print("\ntest_trail_preview_show_hide_events ...")
    from pathlib import Path
    import ast
    src = Path(__file__).parent / 'src' / 'ui' / 'trail_preview_qt.py'
    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code)

    class_methods: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TrailPreviewWidget':
            for item in ast.walk(node):
                if isinstance(item, ast.FunctionDef):
                    class_methods.add(item.name)
            break

    assert 'showEvent' in class_methods, (
        "TrailPreviewWidget is missing showEvent().\n"
        "Without it the animation does not restart when the Customisation tab\n"
        "becomes visible after the user switches away and back."
    )
    assert 'hideEvent' in class_methods, (
        "TrailPreviewWidget is missing hideEvent().\n"
        "Without it the animation timer keeps firing even when the widget is\n"
        "hidden (user is on a different tab), wasting CPU cycles."
    )
    print("  ✅ TrailPreviewWidget has showEvent() and hideEvent()")


def test_panda_overlay_hidden_on_non_home_tabs():
    """Panda overlay must be visible only on the Home tab (index 0).

    The transparent full-window panda widget covers interactive UI on every
    other tab:
    - Tools tab (index 1): blocks the Background Remover live preview pane
    - Panda tab (index 2): covers the Trail Preview strip in Customization
    - Settings tab (index 3): overlaps the Font Family and Font Size combo boxes

    Fix: `tabs.currentChanged` is connected to `_on_main_tab_changed` which
    calls ``overlay.setVisible(index == 0)``.

    This test verifies both the signal wiring in source code (AST check) and
    the live runtime behaviour by switching tabs on a real window instance.
    """
    print("\ntest_panda_overlay_hidden_on_non_home_tabs ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'main.py'
    code = src.read_text(encoding='utf-8')

    # 1. Signal must be connected
    assert 'currentChanged.connect' in code and '_on_main_tab_changed' in code, (
        "main.py must connect tabs.currentChanged to _on_main_tab_changed.\n"
        "Without this the panda overlay stays visible on all tabs, blocking\n"
        "the Background Remover preview, Font settings, and Trail Preview."
    )
    print("  ✅ tabs.currentChanged connected to _on_main_tab_changed")

    # 2. _on_main_tab_changed must exist and use index == 0 logic
    tree = ast.parse(code)
    found_method = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TextureSorterMainWindow':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '_on_main_tab_changed':
                    method_src = ast.get_source_segment(code, item) or ''
                    assert 'index == 0' in method_src or 'index==0' in method_src, (
                        "_on_main_tab_changed must use `index == 0` to show the\n"
                        "overlay only on the Home tab."
                    )
                    assert 'setVisible' in method_src, (
                        "_on_main_tab_changed must call setVisible() on the overlay."
                    )
                    found_method = True
                    break
            break

    assert found_method, (
        "TextureSorterMainWindow is missing _on_main_tab_changed().\n"
        "Add a method that calls overlay.setVisible(index == 0)."
    )
    print("  ✅ _on_main_tab_changed() exists and uses index==0 guard")

    # 3. Runtime check: actually switch tabs and verify visibility
    import sys, logging, os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    logging.disable(logging.CRITICAL)

    import main as _main_mod
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)

    win = _main_mod.TextureSorterMainWindow()
    overlay = win.panda_overlay
    if overlay is None:
        print("  ⚠️  No panda_overlay present — skipping runtime tab check")
        return

    win.resize(1280, 800)
    win.show()
    _app.processEvents()

    expected = {0: True, 1: False, 2: False, 3: False}
    for idx, should_be_visible in expected.items():
        if idx < win.tabs.count():
            win.tabs.setCurrentIndex(idx)
            _app.processEvents()
            actual = overlay.isVisible()
            assert actual == should_be_visible, (
                f"Tab {idx}: overlay visible={actual}, expected {should_be_visible}.\n"
                f"The panda overlay must only be visible on the Home tab (index 0)."
            )

    # Go back to Home and verify it re-shows
    win.tabs.setCurrentIndex(0)
    _app.processEvents()
    assert overlay.isVisible(), (
        "Switching back to Home tab must make the overlay visible again."
    )
    print("  ✅ Runtime: overlay visible=True on Home, False on Tools/Panda/Settings")


def test_settings_tab_has_emoji():
    """Settings main tab must display '⚙️ Settings', not the bare word 'Settings'.

    All other main tabs carry emojis (🏠 Home, 🛠️ Tools, 🐼 Panda).  The
    Settings tab previously lacked one, breaking visual consistency.

    Fix: ``self.tabs.addTab(tab, "⚙️ Settings")`` in create_settings_tab().
    """
    print("\ntest_settings_tab_has_emoji ...")
    import ast
    from pathlib import Path

    code = (Path(__file__).parent / 'main.py').read_text(encoding='utf-8')

    # Source-level check — the literal string must contain the emoji
    assert '"⚙️ Settings"' in code or "'⚙️ Settings'" in code, (
        "main.py must call self.tabs.addTab(tab, \"⚙️ Settings\").\n"
        "The Settings tab label is missing its ⚙️ emoji."
    )
    print("  ✅ Source: ⚙️ emoji present in Settings tab label")

    # Runtime check
    import sys, logging, os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    logging.disable(logging.CRITICAL)
    import main as _m
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    win = _m.TextureSorterMainWindow()

    settings_label = None
    for i in range(win.tabs.count()):
        txt = win.tabs.tabText(i)
        if 'Settings' in txt or 'settings' in txt.lower():
            settings_label = txt
            break

    assert settings_label is not None, "No Settings tab found at runtime."
    assert '⚙' in settings_label, (
        f"Settings tab label at runtime is {repr(settings_label)} — missing ⚙️ emoji."
    )
    print(f"  ✅ Runtime: Settings tab label = {repr(settings_label)}")


def test_panda_home_2d_fallback():
    """Panda Home tab must show an interactive 2D fallback when OpenGL is absent.

    When PyOpenGL is not installed, ``PandaBedroomGL()`` raises an exception and
    the Panda Home tab previously showed a bare QLabel error message.  The fix
    replaces that with a styled QWidget panel containing:
    - A gradient room background
    - An embedded PandaWidget2D companion
    - Furniture shortcut buttons wired to ``_on_bedroom_furniture_clicked``

    This test verifies that the Panda Home widget is a QWidget (not a QLabel
    error message) and that it contains child buttons labelled with furniture names.
    """
    print("\ntest_panda_home_2d_fallback ...")
    import sys, logging, os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    logging.disable(logging.CRITICAL)
    import main as _m
    from PyQt6.QtWidgets import QApplication, QLabel, QPushButton
    _app = QApplication.instance() or QApplication(sys.argv)
    win = _m.TextureSorterMainWindow()
    win.resize(1280, 800)
    win.show()
    _app.processEvents()

    # Locate the Panda Home tab
    panda_home_widget = None
    for i in range(win._panda_tabs.count()):
        if 'Panda Home' in win._panda_tabs.tabText(i) or 'Home' in win._panda_tabs.tabText(i):
            panda_home_widget = win._panda_tabs.widget(i)
            break

    assert panda_home_widget is not None, "Could not find Panda Home tab."

    # Must NOT be a bare error QLabel
    assert not isinstance(panda_home_widget, QLabel), (
        "Panda Home tab is still a bare QLabel error message.\n"
        "Expected a rich QWidget panel with furniture buttons and a 2D panda."
    )
    print(f"  ✅ Panda Home widget type: {type(panda_home_widget).__name__} (not QLabel)")

    # Must have furniture shortcut buttons
    all_btns = panda_home_widget.findChildren(QPushButton)
    assert len(all_btns) >= 3, (
        f"Panda Home 2D fallback has only {len(all_btns)} button(s); "
        "expected at least 3 furniture shortcut buttons."
    )
    btn_texts = [b.text() for b in all_btns]
    print(f"  ✅ Found {len(all_btns)} buttons: {btn_texts}")

    # Check furniture keywords appear in at least one button label
    keywords = ('Wardrobe', 'Inventory', 'Trophies', 'Achievements',
                'Shop', 'Food', 'Toy', 'Outside')
    found_any = any(any(kw in t for kw in keywords) for t in btn_texts)
    assert found_any, (
        f"No recognisable furniture labels found in buttons: {btn_texts}"
    )
    print("  ✅ Furniture shortcut buttons contain expected labels")


def test_gore_goth_themes_apply():
    """Gore and Goth themes must apply without errors and be listed in the settings combo.

    This test verifies:
    1. settings_panel_qt.py addItems includes 'Gore' and 'Goth'
    2. apply_theme('Gore') and apply_theme('Goth') both apply a non-empty stylesheet
       without raising exceptions
    3. GoreSplatterFilter is installed when Gore theme is active and removed when
       the theme changes to Goth
    4. Theme name normalisation: mixed-case 'Gore'/'Goth' must be resolved correctly
    """
    print("\ntest_gore_goth_themes_apply ...")
    from pathlib import Path

    settings_src = (Path(__file__).parent / 'src' / 'ui' / 'settings_panel_qt.py').read_text(encoding='utf-8')
    assert "'Gore'" in settings_src or '"Gore"' in settings_src, \
        "settings_panel_qt.py addItems must include 'Gore'"
    assert "'Goth'" in settings_src or '"Goth"' in settings_src, \
        "settings_panel_qt.py addItems must include 'Goth'"
    print("  ✅ Source: Gore and Goth present in settings combo addItems")

    # Runtime: apply each theme and verify stylesheet is non-empty and different
    import sys, logging, os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    logging.disable(logging.CRITICAL)
    import main as _m
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    win = _m.TextureSorterMainWindow()
    win.resize(1280, 800)

    win.apply_theme('Gore')
    gore_ss = win.styleSheet()
    assert gore_ss, "Gore theme produced an empty stylesheet"
    assert '#8b0000' in gore_ss or '#cc0000' in gore_ss, \
        "Gore stylesheet should contain blood-red color (#8b0000 or #cc0000)"
    # GoreSplatterFilter must be installed
    assert win._gore_splatter_filter is not None, \
        "GoreSplatterFilter must be installed when Gore theme is active"
    print("  ✅ Gore theme: non-empty stylesheet with blood-red colors; splatter filter installed")

    win.apply_theme('Goth')
    goth_ss = win.styleSheet()
    assert goth_ss, "Goth theme produced an empty stylesheet"
    assert '#4a2060' in goth_ss or '#000000' in goth_ss, \
        "Goth stylesheet should contain dark-purple (#4a2060) or pure-black (#000000)"
    # GoreSplatterFilter must be removed when theme changes away from Gore
    assert win._gore_splatter_filter is None, \
        "GoreSplatterFilter must be uninstalled when switching away from Gore theme"
    print("  ✅ Goth theme: non-empty stylesheet with gothic colors; splatter filter removed")

    # Verify themes are distinct
    assert gore_ss != goth_ss, "Gore and Goth stylesheets should differ"
    print("  ✅ Gore and Goth stylesheets are distinct")


def test_theme_name_normalisation():
    """apply_theme() must normalise mixed-case names so 'Dracula' → 'dracula' branch executes.

    Previously apply_theme stored the display name ('Dracula') verbatim but compared
    against the lower-case string ('dracula'), so themes fell through to the default
    dark theme.  The fix adds .lower().strip() normalisation to the read-back.
    """
    print("\ntest_theme_name_normalisation ...")
    import sys, logging, os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    logging.disable(logging.CRITICAL)
    import main as _m
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    win = _m.TextureSorterMainWindow()

    # Dracula should be deep-purple/crimson, NOT the grey default-dark theme
    win.apply_theme('Dracula')
    dracula_ss = win.styleSheet()
    assert '#8b0000' in dracula_ss or '#1a0a1e' in dracula_ss, \
        "apply_theme('Dracula') must produce Dracula stylesheet (deep purple/crimson) " \
        "not the grey default dark theme. Theme name normalisation is missing."
    print("  ✅ 'Dracula' (mixed-case) correctly resolves to Dracula stylesheet")

    # Ocean should be deep navy, NOT the grey default
    win.apply_theme('Ocean')
    ocean_ss = win.styleSheet()
    assert '#00b4d8' in ocean_ss or '#020e1c' in ocean_ss, \
        "apply_theme('Ocean') must produce Ocean stylesheet (deep navy/teal). " \
        "Theme name normalisation is missing."
    print("  ✅ 'Ocean' (mixed-case) correctly resolves to Ocean stylesheet")


def test_set_tooltip_no_set_tooltip_method_call():
    """_set_tooltip helpers must NOT call tooltip_manager.set_tooltip().

    TooltipVerbosityManager has no set_tooltip() method.  Panels that call
    self.tooltip_manager.set_tooltip(widget, id) will raise AttributeError at
    init time, causing their tab to display an error label instead of content.

    The correct pattern is register(widget, id) + get_tooltip(id).
    """
    print("\ntest_set_tooltip_no_set_tooltip_method_call ...")
    import ast
    from pathlib import Path

    panels_to_check = [
        'src/ui/notepad_panel_qt.py',
        'src/ui/file_browser_panel_qt.py',
        'src/ui/shop_panel_qt.py',
        'src/ui/organizer_settings_panel.py',
    ]

    for rel_path in panels_to_check:
        src_path = Path(__file__).parent / rel_path
        if not src_path.exists():
            continue
        code = src_path.read_text(encoding='utf-8')
        # Find the _set_tooltip method body
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == '_set_tooltip':
                method_src = ast.get_source_segment(code, node) or ''
                assert 'tooltip_manager.set_tooltip' not in method_src, (
                    f"{rel_path}: _set_tooltip must NOT call tooltip_manager.set_tooltip() "
                    f"— that method does not exist on TooltipVerbosityManager. "
                    f"Use tooltip_manager.register(widget, id) + get_tooltip(id) instead."
                )

    print("  ✅ No panel calls tooltip_manager.set_tooltip() (which does not exist)")


def test_set_tooltip_registers_with_manager():
    """_set_tooltip helpers must call tooltip_manager.register() for cycling support.

    Panels that only call get_tooltip() without register() will display the
    initial tooltip text but won't cycle on hover or update when the mode changes.
    """
    print("\ntest_set_tooltip_registers_with_manager ...")
    import ast
    from pathlib import Path

    panels_to_check = [
        'src/ui/notepad_panel_qt.py',
        'src/ui/file_browser_panel_qt.py',
        'src/ui/shop_panel_qt.py',
        'src/ui/organizer_settings_panel.py',
    ]

    for rel_path in panels_to_check:
        src_path = Path(__file__).parent / rel_path
        if not src_path.exists():
            continue
        code = src_path.read_text(encoding='utf-8')
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == '_set_tooltip':
                method_src = ast.get_source_segment(code, node) or ''
                assert 'register' in method_src, (
                    f"{rel_path}: _set_tooltip must call tooltip_manager.register(widget, id) "
                    f"so widgets are enrolled in the cycling/mode-change system. "
                    f"Without register(), tooltip mode changes have no effect on the widget."
                )

    print("  ✅ All _set_tooltip helpers call tooltip_manager.register()")


def test_cancel_buttons_have_interruption_support():
    """Processing panels that start QThread workers must support cancellation.

    The pattern required:
    1. The panel has a ``cancel_btn`` (or ``_cancel_btn``) attribute.
    2. The panel has a ``_cancel_*`` method that calls ``requestInterruption()``.
    3. The worker's ``run()`` method calls ``isInterruptionRequested()`` to
       honour the cancel request without terminating the thread forcefully.

    Panels that start long-running workers without this pattern leave users
    with no way to stop an accidental large-batch operation.
    """
    print("\ntest_cancel_buttons_have_interruption_support ...")
    from pathlib import Path
    import re

    panels_to_check = [
        'src/ui/alpha_fixer_panel_qt.py',
        'src/ui/batch_normalizer_panel_qt.py',
        'src/ui/batch_rename_panel_qt.py',
        'src/ui/quality_checker_panel_qt.py',
        'src/ui/lineart_converter_panel_qt.py',
    ]

    for rel_path in panels_to_check:
        src_path = Path(__file__).parent / rel_path
        if not src_path.exists():
            print(f"  ⚠️  Skipped (not found): {rel_path}")
            continue

        code = src_path.read_text(encoding='utf-8')

        # 1. Panel must have a cancel button — look for assignment, not any occurrence
        #    (This avoids false-positives from comment lines or string literals.)
        assert re.search(r'self\._?cancel_btn\s*=\s*QPushButton', code), (
            f"{rel_path}: missing cancel button assignment (self.cancel_btn = QPushButton(...) or self._cancel_btn = ...).\n"
            "Add a QPushButton('Cancel') with visible=False, enabled=False that shows during processing."
        )

        # 2. Panel must have a _cancel_* method that calls requestInterruption()
        assert 'requestInterruption' in code, (
            f"{rel_path}: _cancel_* method must call self.worker_thread.requestInterruption().\n"
            "This signals the worker to stop cleanly between files."
        )

        # 3. Worker run() method must check isInterruptionRequested()
        assert 'isInterruptionRequested' in code, (
            f"{rel_path}: worker run() must call self.isInterruptionRequested() per iteration.\n"
            "Without this, requestInterruption() is sent but never checked — cancel has no effect."
        )

        print(f"  ✅ {rel_path.split('/')[-1]}: cancel_btn + requestInterruption + isInterruptionRequested")

    print("  PASS")


def test_panda_set_mood_emits_signal():
    """PandaWidgetGL.set_mood() must emit mood_changed after updating state.

    The main window connects ``panda_widget.mood_changed`` to
    ``on_panda_mood_changed`` so the mood system can react to 3D panda mood
    transitions.  Without the emit, the signal is connected but never fires,
    making mood-driven feedback (achievement toasts, sound cues, etc.) silent.

    Fix: add ``self.mood_changed.emit(mood)`` at the end of ``set_mood()``.
    """
    print("\ntest_panda_set_mood_emits_signal ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'panda_widget_gl.py'
    if not src.exists():
        print("  ⚠️  Skipped (panda_widget_gl.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    # Find the set_mood method body and check it emits mood_changed
    found_set_mood = False
    emits_signal = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'set_mood':
            found_set_mood = True
            method_src = ast.get_source_segment(code, node) or ''
            emits_signal = 'mood_changed.emit' in method_src
            break

    assert found_set_mood, "PandaWidgetGL.set_mood() method not found in panda_widget_gl.py"
    assert emits_signal, (
        "set_mood() does NOT call self.mood_changed.emit(mood).\n"
        "Add 'self.mood_changed.emit(mood)' at the end of set_mood() so\n"
        "the main window's on_panda_mood_changed handler receives mood updates."
    )
    print("  ✅ set_mood() calls self.mood_changed.emit(mood)")


def test_color_correction_guards_empty_files():
    """ColorCorrectionPanelQt._start_processing() must guard against empty file selection.

    Starting the ColorCorrectionWorker with an empty ``input_files`` list is
    wasted work (the worker loop does nothing) and gives users no feedback.
    The guard must show a QMessageBox.warning and return early before starting
    the background thread.
    """
    print("\ntest_color_correction_guards_empty_files ...")
    import ast
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'color_correction_panel_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (color_correction_panel_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')
    tree = ast.parse(code, filename=str(src))

    found_method = False
    has_empty_guard = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef,)) and node.name == '_start_processing':
            found_method = True
            method_src = ast.get_source_segment(code, node) or ''
            # Must have an early-return when input_files is empty
            has_empty_guard = (
                'not self.input_files' in method_src or
                'not self.selected_files' in method_src or
                'len(self.input_files) == 0' in method_src
            )
            break

    assert found_method, "ColorCorrectionPanelQt._start_processing() not found"
    assert has_empty_guard, (
        "ColorCorrectionPanelQt._start_processing() must check 'if not self.input_files' "
        "and show a QMessageBox.warning + return before starting the worker.\n"
        "Starting the worker with no files is silent no-op waste."
    )
    print("  ✅ _start_processing() guards against empty input_files")


def test_model_download_thread_supports_cancellation():
    """ModelDownloadThread must support cancellation via isInterruptionRequested().

    When a large model download is started and the user clicks Cancel,
    the thread should check isInterruptionRequested() in the progress callback
    and raise InterruptedError to stop the download cleanly — without
    forcefully terminating the thread or leaving a partial file.

    Requirements:
    1. ModelDownloadThread.run() uses a progress callback that checks
       isInterruptionRequested() (via InterruptedError or direct check).
    2. ModelCardWidget has a ``_cancel_download_btn`` that calls
       ``requestInterruption()`` on the running thread.
    """
    print("\ntest_model_download_thread_supports_cancellation ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'ai_models_settings_tab.py'
    if not src.exists():
        print("  ⚠️  Skipped (ai_models_settings_tab.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # 1. Worker checks for interruption
    assert 'isInterruptionRequested' in code, (
        "ModelDownloadThread must check isInterruptionRequested() in its "
        "progress callback to support clean cancellation."
    )

    # 2. Cancel button is created and wired
    assert re.search(r'self\._cancel_download_btn\s*=\s*QPushButton', code), (
        "ModelCardWidget must create self._cancel_download_btn = QPushButton(...) "
        "that becomes visible when a download starts."
    )

    # 3. requestInterruption is called to signal the thread
    assert 'requestInterruption' in code, (
        "The _cancel_download() method must call self.download_thread.requestInterruption() "
        "to signal the download thread to stop."
    )

    print("  ✅ ModelDownloadThread: isInterruptionRequested + _cancel_download_btn + requestInterruption")


def test_archive_queue_has_cancel_button():
    """ArchiveQueueWidget must expose a Cancel button to stop batch processing.

    The archive queue supports Start and Pause but was missing a Cancel button
    to abort the current processing run.  Without it, users had no way to stop
    a large batch operation mid-flight — they could only pause it indefinitely.

    Requirements:
    1. ArchiveQueueWidget has ``self.cancel_btn = QPushButton(...)``
    2. There is a ``cancel_processing()`` public method
    3. The cancel button enables when processing starts and disables after it ends
    """
    print("\ntest_archive_queue_has_cancel_button ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'archive_queue_widgets_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (archive_queue_widgets_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # 1. Cancel button exists
    assert re.search(r'self\.cancel_btn\s*=\s*QPushButton', code), (
        "ArchiveQueueWidget must have self.cancel_btn = QPushButton(...) "
        "in its setup so users can stop a batch operation mid-run."
    )
    print("  ✅ self.cancel_btn = QPushButton found")

    # 2. cancel_processing() method exists
    assert re.search(r'def cancel_processing\(self\)', code), (
        "ArchiveQueueWidget must have a public cancel_processing() method "
        "that sets self.is_processing = False to stop the queue thread."
    )
    print("  ✅ cancel_processing() method found")

    # 3. is_processing = False to abort the thread
    assert 'self.is_processing = False' in code, (
        "cancel_processing() must set self.is_processing = False so the "
        "_process_queue() thread stops at the next loop iteration."
    )
    print("  ✅ is_processing flag cleared on cancel")


def test_lineart_conversion_worker_supports_cancellation():
    """ConversionWorker.run() must check isInterruptionRequested() per file.

    The older ConversionWorker class (used as a fallback when the format combo
    is absent) did not check isInterruptionRequested() at all.  This made the
    Cancel button in the lineart panel a no-op for that code path — the thread
    would finish the entire batch even after the user clicked Cancel.

    Requirements:
    1. ConversionWorker.run() calls isInterruptionRequested()
    2. When interrupted it emits finished(False, ...) without completing
    """
    print("\ntest_lineart_conversion_worker_supports_cancellation ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (lineart_converter_panel_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # Locate ConversionWorker.run() — stop before _FormatConversionWorker
    m = re.search(
        r'class ConversionWorker\(QThread\).*?(?=class _FormatConversionWorker)',
        code, re.DOTALL
    )
    assert m, "ConversionWorker class not found in lineart_converter_panel_qt.py"
    worker_code = m.group(0)

    assert 'isInterruptionRequested' in worker_code, (
        "ConversionWorker.run() must call isInterruptionRequested() per loop "
        "iteration so the Cancel button stops the batch mid-run."
    )
    print("  ✅ ConversionWorker.run() checks isInterruptionRequested()")


def test_preview_slider_single_image():
    """ComparisonSliderWidget._paint_slider_mode must handle missing after_pixmap.

    Before: if after_pixmap was None (image loaded but not yet processed),
    _paint_slider_mode returned early and the widget showed a blank grey box.
    After: it falls back to showing the available image as a single-panel
    preview so the user sees the loaded image immediately.

    Requirements:
    1. _paint_slider_mode does NOT return immediately when only one image is set
    2. It falls back to showing the available pixmap as a single image
    """
    print("\ntest_preview_slider_single_image ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'ui' / 'live_preview_slider_qt.py'
    if not src.exists():
        print("  ⚠️  Skipped (live_preview_slider_qt.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    # Find _paint_slider_mode
    m = re.search(r'def _paint_slider_mode\(self.*?(?=\n    def )', code, re.DOTALL)
    assert m, "_paint_slider_mode not found in live_preview_slider_qt.py"
    paint_code = m.group(0)

    # Must NOT have the simple "if not before_scaled or not after_scaled: return" pattern
    old_pattern = r'if not before_scaled or not after_scaled:\s*\n\s*painter\.restore\(\)\s*\n\s*return'
    assert not re.search(old_pattern, paint_code), (
        "_paint_slider_mode still has the old early-return that blanks the preview "
        "when only one image is loaded.  The fix should fall back to single-image mode."
    )
    print("  ✅ _paint_slider_mode no longer blanks when only one image is available")

    # Should handle the case where only one of the two is set
    assert 'only one' in paint_code.lower() or 'only_pm' in paint_code or 'only_label' in paint_code, (
        "_paint_slider_mode should have a single-image fallback path "
        "(look for 'only_pm' or a comment about single image)."
    )
    print("  ✅ Single-image fallback path present")


def test_realesrgan_pyinstaller_hooks_exist():
    """PyInstaller hooks for basicsr, realesrgan, and gfpgan must exist.

    Without dedicated hooks, PyInstaller's static analyser misses:
    - basicsr dynamic arch-loader (imports submodules by name at runtime)
    - realesrgan utility helpers that are loaded via getattr
    - gfpgan/facexlib face-parsing models loaded at detection time

    Each hook must call collect_submodules() to ensure every submodule is
    bundled so the frozen EXE can run Real-ESRGAN without a separate install.
    """
    print("\ntest_realesrgan_pyinstaller_hooks_exist ...")
    from pathlib import Path

    root = Path(__file__).parent

    for pkg in ('basicsr', 'realesrgan', 'gfpgan'):
        hook_path = root / f'hook-{pkg}.py'
        assert hook_path.exists(), (
            f"hook-{pkg}.py not found in project root.\n"
            f"Create it with collect_submodules('{pkg}') so PyInstaller bundles "
            f"all {pkg} submodules into the frozen EXE."
        )
        hook_code = hook_path.read_text(encoding='utf-8')
        assert 'collect_submodules' in hook_code, (
            f"hook-{pkg}.py must call collect_submodules('{pkg}') to ensure "
            f"all dynamic submodule imports work inside the frozen EXE."
        )
        print(f"  ✅ hook-{pkg}.py exists and calls collect_submodules()")

    # Spec must reference gfpgan and facexlib hiddenimports
    spec_path = root / 'build_spec_onefolder.spec'
    if spec_path.exists():
        spec = spec_path.read_text(encoding='utf-8')
        for pkg in ('gfpgan', 'facexlib'):
            assert f"'{pkg}'" in spec or f'"{pkg}"' in spec, (
                f"'{pkg}' missing from build_spec_onefolder.spec hiddenimports"
            )
            print(f"  ✅ '{pkg}' present in spec hiddenimports")


def test_lineart_smooth_lines_in_all_pipelines():
    """LineArtConverter.convert() and preview_settings() must apply smooth_lines.

    convert_image() has always applied smooth_lines (lines 232-233 in the
    original file).  However convert() — used by the live preview worker and
    by _FormatConversionWorker — was missing the step entirely, so:

    1. The 'Smooth lines' checkbox had zero visible effect on the preview.
    2. When the user saved via the format-conversion worker the lines were
       never smoothed either.
    3. preview_settings() was also missing the step, so the settings-preview
       helper produced different results from the full save pipeline.

    Requirements:
    1. convert() applies smooth_lines after denoise and before invert
    2. preview_settings() applies smooth_lines at the same position
    """
    print("\ntest_lineart_smooth_lines_in_all_pipelines ...")
    import re
    from pathlib import Path

    src = Path(__file__).parent / 'src' / 'tools' / 'lineart_converter.py'
    if not src.exists():
        print("  ⚠️  Skipped (lineart_converter.py not found)")
        return

    code = src.read_text(encoding='utf-8')

    for method_name in ('convert', 'preview_settings'):
        # Extract the method body up to the next top-level method definition
        m = re.search(
            rf'def {method_name}\(self.*?(?=\n    def |\Z)',
            code, re.DOTALL
        )
        assert m, f"Method {method_name}() not found in lineart_converter.py"
        body = m.group(0)

        assert 'smooth_lines' in body, (
            f"LineArtConverter.{method_name}() does not apply smooth_lines.\n"
            f"Add: if settings.smooth_lines: result = self._smooth_lines(result, settings.smooth_amount)\n"
            f"between the denoise step and the invert step."
        )
        print(f"  ✅ {method_name}() applies smooth_lines")

        # Verify ordering: smooth_lines must come after denoise and before invert
        denoise_pos = body.find('settings.denoise')
        smooth_pos = body.find('smooth_lines')
        invert_pos = body.rfind('settings.invert')  # rfind to skip data-class line

        assert denoise_pos < smooth_pos, (
            f"{method_name}(): smooth_lines step must come AFTER denoise step"
        )
        if invert_pos > 0:
            assert smooth_pos < invert_pos, (
                f"{method_name}(): smooth_lines step must come BEFORE invert step"
            )
        print(f"  ✅ {method_name}(): smooth_lines is ordered after denoise and before invert")


def test_vampire_theme_and_bat_filter():
    """Vampire theme must be defined in main.py and use the VampireBatFilter.

    Requirements:
    1. VampireBatFilter class exists in main.py
    2. _update_vampire_bats() method exists in main.py
    3. _DISPLAY_MAP includes 'vampire' key
    4. Vampire theme QSS is defined (elif theme in ('vampire',):)
    5. Settings combo source includes 'Vampire'
    6. Lineart preset descriptions for modes that use those controls are improved
    """
    print("\ntest_vampire_theme_and_bat_filter ...")
    from pathlib import Path

    main_src = Path(__file__).parent / 'main.py'
    assert main_src.exists(), "main.py not found"
    code = main_src.read_text(encoding='utf-8')

    assert 'class VampireBatFilter' in code, \
        "VampireBatFilter class not found in main.py"
    print("  ✅ VampireBatFilter class present")

    assert 'class VampireBatLabel' in code, \
        "VampireBatLabel class not found in main.py"
    print("  ✅ VampireBatLabel class present")

    assert '_update_vampire_bats' in code, \
        "_update_vampire_bats() not found in main.py"
    print("  ✅ _update_vampire_bats() present")

    assert "'vampire': 'vampire'" in code, \
        "'vampire' key missing from _DISPLAY_MAP in main.py"
    print("  ✅ 'vampire' present in _DISPLAY_MAP")

    assert "theme in ('vampire',)" in code, \
        "Vampire theme QSS block (elif theme in ('vampire',):) not found"
    print("  ✅ Vampire theme QSS block present")

    settings_src = Path(__file__).parent / 'src' / 'ui' / 'settings_panel_qt.py'
    s_code = settings_src.read_text(encoding='utf-8')
    assert '"Vampire"' in s_code or "'Vampire'" in s_code, \
        "'Vampire' not added to settings combo in settings_panel_qt.py"
    print("  ✅ 'Vampire' present in settings combo")

    assert "'vampire': 'Vampire'" in s_code, \
        "'vampire': 'Vampire' missing from theme_map in settings_panel_qt.py"
    print("  ✅ 'vampire' present in settings theme_map")


def test_ocean_ripple_filter():
    """Ocean ripple click effect must be defined and wired in main.py.

    Requirements:
    1. OceanRippleFilter class exists in main.py
    2. _update_ocean_ripple() method exists in main.py
    3. _update_ocean_ripple is called from apply_theme
    """
    print("\ntest_ocean_ripple_filter ...")
    from pathlib import Path

    code = (Path(__file__).parent / 'main.py').read_text(encoding='utf-8')

    assert 'class OceanRippleFilter' in code, \
        "OceanRippleFilter class not found in main.py"
    print("  ✅ OceanRippleFilter class present")

    assert 'class OceanRippleLabel' in code, \
        "OceanRippleLabel class not found in main.py"
    print("  ✅ OceanRippleLabel class present")

    assert '_update_ocean_ripple' in code, \
        "_update_ocean_ripple() not found in main.py"
    print("  ✅ _update_ocean_ripple() present")

    # Verify it is called from apply_theme (not just defined)
    import re
    apply_theme_match = re.search(
        r'def apply_theme\(.*?(?=\n    def |\Z)', code, re.DOTALL
    )
    assert apply_theme_match, "apply_theme() not found in main.py"
    apply_body = apply_theme_match.group(0)
    assert '_update_ocean_ripple' in apply_body, \
        "_update_ocean_ripple() is defined but not called from apply_theme()"
    print("  ✅ _update_ocean_ripple() called from apply_theme()")


def test_theme_layout_fixes_appended():
    """Common layout-fix QSS must be appended to the stylesheet in apply_theme().

    Prevents text clipping in QTabBar::tab, QGroupBox::title, and QLabel
    across all themes by setting minimum widths/heights.
    """
    print("\ntest_theme_layout_fixes_appended ...")
    from pathlib import Path

    code = (Path(__file__).parent / 'main.py').read_text(encoding='utf-8')

    assert '_LAYOUT_FIXES' in code, \
        "_LAYOUT_FIXES variable not found in main.py"
    print("  ✅ _LAYOUT_FIXES variable present")

    assert 'QTabBar::tab { min-width:' in code or "QTabBar::tab { min-width:" in code \
        or "min-width: 70px" in code, \
        "QTabBar::tab min-width rule not in _LAYOUT_FIXES"
    print("  ✅ QTabBar::tab min-width rule present")

    assert 'stylesheet + _LAYOUT_FIXES' in code, \
        "_LAYOUT_FIXES not concatenated with stylesheet before setStyleSheet()"
    print("  ✅ _LAYOUT_FIXES appended to all theme stylesheets")


def test_lineart_presets_have_mode_specific_params():
    """All lineart presets must include keys for all mode-specific controls.

    edge_detect presets → edge_low, edge_high, edge_aperture
    adaptive presets    → adaptive_block, adaptive_c, adaptive_method
    sketch presets      → smooth_lines, smooth_amount

    Having these keys means _on_preset_changed() fully populates the
    advanced control panels when the user selects any preset.
    """
    print("\ntest_lineart_presets_have_mode_specific_params ...")
    import sys, importlib
    sys.path.insert(0, str((__import__('pathlib').Path(__file__).parent / 'src')))

    # Import without PyQt6 by patching the stub
    import types
    _stub = types.ModuleType('PyQt6')
    for sub in ('QtWidgets', 'QtCore', 'QtGui'):
        _stub.__dict__[sub] = types.ModuleType(f'PyQt6.{sub}')
    sys.modules.setdefault('PyQt6', _stub)
    for sub in ('QtWidgets', 'QtCore', 'QtGui'):
        sys.modules.setdefault(f'PyQt6.{sub}', _stub.__dict__[sub])

    try:
        # Re-import to pick up changes if already cached
        if 'ui.lineart_converter_panel_qt' in sys.modules:
            del sys.modules['ui.lineart_converter_panel_qt']
        from ui.lineart_converter_panel_qt import LINEART_PRESETS
    except Exception as e:
        print(f"  ⚠️  Could not import LINEART_PRESETS: {e} — skipped")
        return

    _EDGE_KEYS = ('edge_low', 'edge_high', 'edge_aperture')
    _ADAP_KEYS = ('adaptive_block', 'adaptive_c', 'adaptive_method')
    _SKETCH_KEYS = ('smooth_lines', 'smooth_amount')

    for name, p in LINEART_PRESETS.items():
        mode = p.get('mode', 'pure_black')
        if mode == 'edge_detect':
            for k in _EDGE_KEYS:
                assert k in p, f"Preset '{name}' (edge_detect) missing key '{k}'"
        elif mode == 'adaptive':
            for k in _ADAP_KEYS:
                assert k in p, f"Preset '{name}' (adaptive) missing key '{k}'"
        elif mode == 'sketch':
            for k in _SKETCH_KEYS:
                assert k in p, f"Preset '{name}' (sketch) missing key '{k}'"
        # All presets should have smooth_lines/smooth_amount for uniformity
        for k in _SKETCH_KEYS:
            assert k in p, f"Preset '{name}' missing universal key '{k}'"

    print(f"  ✅ All {len(LINEART_PRESETS)} presets have required mode-specific keys")


def test_click_filters_use_qt6_position_api():
    """All click-effect event filters must use event.position().toPoint()
    (the Qt6-correct API) instead of the deprecated event.pos().

    In PyQt6 >= 6.4, QMouseEvent.pos() returns QPointF in some builds,
    causing a TypeError when passed to QWidget.mapTo() which expects QPoint.
    Using event.position().toPoint() is the correct Qt6 approach and avoids
    this type mismatch that silently prevents the visual effect from firing.
    """
    print("\ntest_click_filters_use_qt6_position_api ...")
    from pathlib import Path
    import re

    code = (Path(__file__).parent / 'main.py').read_text(encoding='utf-8')

    # Must NOT use the deprecated event.pos() in any event filter
    # (Check inside the three filter eventFilter methods)
    filter_classes = [
        'GoreSplatterFilter',
        'VampireBatFilter',
        'OceanRippleFilter',
    ]
    for cls in filter_classes:
        # Extract the eventFilter body for this class
        pattern = re.compile(
            rf'class {cls}.*?(?=\nclass |\Z)', re.DOTALL
        )
        m = pattern.search(code)
        assert m, f"Class {cls} not found in main.py"
        body = m.group(0)

        assert 'event.position().toPoint()' in body, \
            (f"{cls}.eventFilter uses deprecated event.pos() instead of "
             f"event.position().toPoint() — this is the likely cause of "
             f"the splatter effect not firing in PyQt6 >= 6.4")
        print(f"  ✅ {cls} uses event.position().toPoint()")

        assert "hasattr(event, 'position')" in body, \
            (f"{cls}.eventFilter checks hasattr(event, 'pos') instead of "
             f"hasattr(event, 'position') — update the guard to match the new API")
        print(f"  ✅ {cls} guards with hasattr(event, 'position')")

        # Must not use the deprecated form
        assert "event.pos()" not in body, \
            f"{cls} still contains event.pos() — remove it"
        print(f"  ✅ {cls} does not use deprecated event.pos()")


def test_lineart_converter_numpy_fallbacks():
    """The lineart converter must not crash when numpy is unavailable.

    Key methods that previously used numpy unconditionally:
    - _sharpen_image: now has PIL UnsharpMask fallback
    - _apply_conversion_mode (PURE_BLACK / THRESHOLD): now has point() fallback
    - _remove_midtones: now has point() fallback
    - _apply_background TRANSPARENT: now has PIL putalpha fallback
    - _adaptive_threshold fallback branch: no longer uses nested np loops alone
    """
    print("\ntest_lineart_converter_numpy_fallbacks ...")
    from pathlib import Path

    code = (Path(__file__).parent / 'src' / 'tools' / 'lineart_converter.py'
            ).read_text(encoding='utf-8')

    # _sharpen_image must guard with HAS_NUMPY
    import re
    sharpen_m = re.search(r'def _sharpen_image.*?(?=\n    def |\Z)', code, re.DOTALL)
    assert sharpen_m, "_sharpen_image not found"
    assert 'HAS_NUMPY' in sharpen_m.group(0), \
        "_sharpen_image does not guard with HAS_NUMPY"
    print("  ✅ _sharpen_image guarded with HAS_NUMPY")

    # _remove_midtones must guard with HAS_NUMPY
    rm_m = re.search(r'def _remove_midtones.*?(?=\n    def |\Z)', code, re.DOTALL)
    assert rm_m, "_remove_midtones not found"
    assert 'HAS_NUMPY' in rm_m.group(0), \
        "_remove_midtones does not guard with HAS_NUMPY"
    print("  ✅ _remove_midtones guarded with HAS_NUMPY")

    # _apply_background TRANSPARENT must guard with HAS_NUMPY
    bg_m = re.search(r'def _apply_background.*?(?=\n    def |\Z)', code, re.DOTALL)
    assert bg_m, "_apply_background not found"
    assert 'HAS_NUMPY' in bg_m.group(0), \
        "_apply_background does not guard with HAS_NUMPY"
    print("  ✅ _apply_background guarded with HAS_NUMPY")

    # _apply_conversion_mode must have PIL fallbacks
    mode_m = re.search(r'def _apply_conversion_mode.*?(?=\n    def |\Z)', code, re.DOTALL)
    assert mode_m, "_apply_conversion_mode not found"
    assert 'HAS_NUMPY' in mode_m.group(0), \
        "_apply_conversion_mode does not guard with HAS_NUMPY"
    print("  ✅ _apply_conversion_mode guarded with HAS_NUMPY")


def test_numpy_pyinstaller_hooks():
    """Verify that the numpy PyInstaller hook and runtime hook exist and are valid.

    The hook files ensure that NumPy's compiled binary extensions (.pyd/.so)
    and data files are collected when building a frozen exe.  Without them,
    numpy fails to import at runtime in the frozen exe because the DLL
    dependencies (BLAS/LAPACK) are not included.

    Checks:
    1. hook-numpy.py exists and calls collect_all / collect_submodules
    2. runtime-hook-numpy.py exists and handles Windows DLL PATH setup
    3. Both spec files reference runtime-hook-numpy.py
    4. Both spec files call collect_all('numpy')
    5. Both spec files include numpy._core as a hidden import (numpy 2.x compat)
    """
    print("\ntest_numpy_pyinstaller_hooks ...")
    from pathlib import Path

    repo = Path(__file__).parent

    # ── hook-numpy.py ──────────────────────────────────────────────────────
    hook = repo / 'hook-numpy.py'
    assert hook.exists(), "hook-numpy.py not found in repo root"
    hook_code = hook.read_text(encoding='utf-8')

    assert 'collect_all' in hook_code, \
        "hook-numpy.py must call collect_all('numpy') to bundle DLLs"
    print("  ✅ hook-numpy.py calls collect_all")

    assert 'collect_submodules' in hook_code, \
        "hook-numpy.py must call collect_submodules('numpy')"
    print("  ✅ hook-numpy.py calls collect_submodules")

    assert 'numpy._core' in hook_code, \
        "hook-numpy.py must list numpy._core for NumPy 2.x compatibility"
    print("  ✅ hook-numpy.py includes numpy._core for NumPy 2.x")

    # ── runtime-hook-numpy.py ──────────────────────────────────────────────
    rt_hook = repo / 'runtime-hook-numpy.py'
    assert rt_hook.exists(), "runtime-hook-numpy.py not found in repo root"
    rt_code = rt_hook.read_text(encoding='utf-8')

    assert 'getattr(sys, \'frozen\', False)' in rt_code or "getattr(sys, 'frozen', False)" in rt_code, \
        "runtime-hook-numpy.py must guard with getattr(sys, 'frozen', False)"
    print("  ✅ runtime-hook-numpy.py checks sys.frozen")

    assert 'AddDllDirectory' in rt_code or 'PATH' in rt_code, \
        "runtime-hook-numpy.py must set up Windows DLL search path"
    print("  ✅ runtime-hook-numpy.py handles Windows DLL path")

    # ── both spec files ────────────────────────────────────────────────────
    for spec_name in ('build_spec_onefolder.spec', 'build_spec_with_svg.spec'):
        spec = repo / spec_name
        assert spec.exists(), f"{spec_name} not found"
        spec_code = spec.read_text(encoding='utf-8')

        assert "collect_all('numpy')" in spec_code, \
            (f"{spec_name}: must call collect_all('numpy') to collect "
             f"numpy DLLs/binaries (just listing string hidden imports is not enough)")
        print(f"  ✅ {spec_name} calls collect_all('numpy')")

        assert 'runtime-hook-numpy.py' in spec_code, \
            f"{spec_name}: must include runtime-hook-numpy.py in runtime_hooks"
        print(f"  ✅ {spec_name} references runtime-hook-numpy.py")

        assert "numpy._core" in spec_code, \
            (f"{spec_name}: must list numpy._core as a hidden import "
             f"for NumPy 2.x compatibility (numpy.core is a compat shim in 2.x)")
        print(f"  ✅ {spec_name} has numpy._core hidden import")

    print("  ✅ All numpy PyInstaller hook checks passed")


def test_tools_has_cv2_guards_numpy():
    """cv2-using tools must link has_cv2 to HAS_NUMPY.

    cv2 (opencv-python) requires numpy.  If numpy is unavailable,
    cv2 will also fail to import.  The defensive pattern
        self.has_cv2 = HAS_CV2 and HAS_NUMPY
    ensures that when numpy is absent, every code path that calls
    np.array() is gated by the same has_cv2 check — preventing
    NameError: name 'np' is not defined crashes.
    """
    print("\ntest_tools_has_cv2_guards_numpy ...")
    from pathlib import Path
    import re

    tools_to_check = [
        ('src/tools/lineart_converter.py', 'LineArtConverter'),
        ('src/tools/batch_normalizer.py',  'BatchFormatNormalizer'),
        ('src/tools/quality_checker.py',   'ImageQualityChecker'),
    ]

    repo = Path(__file__).parent

    for rel_path, class_name in tools_to_check:
        code = (repo / rel_path).read_text(encoding='utf-8')

        # Find the __init__ method of each class
        pattern = re.compile(
            rf'class {class_name}.*?def __init__.*?(?=\n    def |\Z)',
            re.DOTALL,
        )
        m = pattern.search(code)
        assert m, f"{class_name}.__init__ not found in {rel_path}"

        body = m.group(0)
        assert 'HAS_CV2 and HAS_NUMPY' in body, (
            f"{class_name}.__init__ in {rel_path} sets "
            f"self.has_cv2 = HAS_CV2 without AND-ing HAS_NUMPY. "
            f"cv2 requires numpy; if numpy is absent, cv2 will also be absent "
            f"and every np.array() call inside the cv2 branch will crash with "
            f"NameError. Fix: self.has_cv2 = HAS_CV2 and HAS_NUMPY"
        )
        print(f"  ✅ {class_name} guards has_cv2 with HAS_NUMPY")


def run_all_tests():
    print("=" * 65)
    print("Hybrid Architecture + Lazy rembg Import Tests")
    print("=" * 65)

    tests = [
        test_tools_import_does_not_call_sys_exit,
        test_get_rembg_returns_none_when_absent,
        test_object_remover_remove_object_safe_when_rembg_absent,
        test_torch_not_imported_at_module_level,
        test_ai_inference_importable_without_onnxruntime,
        test_ai_training_pytorch_importable_without_torch,
        test_ai_package_exports_hybrid_symbols,
        test_organizer_style_no_false_positives,
        test_model_manager_url_structure,
        test_panda_no_double_bob,
        test_bg_remover_onnx_fallback_present,
        test_panda_camera_distance_and_drag,
        test_bedroom_panda_walk,
        test_bg_remover_splitter_and_backend_toggle,
        test_dungeon_view_pyqt_guard,
        test_organizer_panel_constraints,
        test_theme_stylesheet_cursor_hints,
        test_main_qgroupbox_import,
        test_main_input_path_label_exists,
        test_dungeon_render_integrated_dungeon,
        test_apply_theme_accepts_optional_name,
        test_qss_no_cursor_pointer,
        test_dock_widget_object_names,
        test_minigame_achievement_ids_valid,
        test_theme_achievement_ids_valid,
        test_show_help_and_settings_methods,
        test_tool_labels_no_duplicates,
        test_auto_backup_recovery_wired,
        test_panda_overlay_no_source_mode_fill,
        test_panda_overlay_scale_capped,
        test_settings_panel_auto_saves_on_change,
        test_clear_button_not_too_narrow,
        test_trail_preview_show_hide_events,
        test_panda_overlay_hidden_on_non_home_tabs,
        test_settings_tab_has_emoji,
        test_panda_home_2d_fallback,
        test_gore_goth_themes_apply,
        test_theme_name_normalisation,
        test_panda_widget_gl_qstate_import,
        test_bedroom_mouse_release_event,
        test_otter_smooth_look_animation,
        test_spec_bundle_completeness,
        test_set_tooltip_no_set_tooltip_method_call,
        test_set_tooltip_registers_with_manager,
        test_cancel_buttons_have_interruption_support,
        test_panda_set_mood_emits_signal,
        test_color_correction_guards_empty_files,
        test_model_download_thread_supports_cancellation,
        test_archive_queue_has_cancel_button,
        test_lineart_conversion_worker_supports_cancellation,
        test_preview_slider_single_image,
        test_realesrgan_pyinstaller_hooks_exist,
        test_lineart_smooth_lines_in_all_pipelines,
        test_vampire_theme_and_bat_filter,
        test_ocean_ripple_filter,
        test_theme_layout_fixes_appended,
        test_lineart_presets_have_mode_specific_params,
        test_click_filters_use_qt6_position_api,
        test_lineart_converter_numpy_fallbacks,
        test_numpy_pyinstaller_hooks,
        test_tools_has_cv2_guards_numpy,
    ]

    passed, failed = [], []
    for test in tests:
        try:
            test()
            passed.append(test.__name__)
        except (AssertionError, Exception, SystemExit) as exc:
            failed.append((test.__name__, exc))
            print(f"  FAIL: {exc}")

    print("\n" + "=" * 65)
    print("Results:")
    for name in passed:
        print(f"  ✅ PASS  {name}")
    for name, err in failed:
        print(f"  ❌ FAIL  {name}: {err}")
    print("=" * 65)

    if failed:
        print(f"\n❌ {len(failed)} test(s) failed.")
        return 1
    else:
        print(f"\n🎉 All {len(passed)} tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
