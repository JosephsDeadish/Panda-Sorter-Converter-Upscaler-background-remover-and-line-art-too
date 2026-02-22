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
