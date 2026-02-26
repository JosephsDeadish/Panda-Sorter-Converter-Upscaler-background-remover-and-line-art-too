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
        test_panda_widget_gl_qstate_import,
        test_bedroom_mouse_release_event,
        test_otter_smooth_look_animation,
        test_spec_bundle_completeness,
    ]

    passed, failed = [], []
    for test in tests:
        try:
            test()
            passed.append(test.__name__)
        except (AssertionError, Exception) as exc:
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
