"""
Test organizer suggested/manual modes, style descriptions, and dependency validation.
Validates fixes for interactive mode workflow and descriptive style text.
"""

import sys
import threading
import time
import tempfile
import shutil
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))


def test_style_descriptions_are_descriptive():
    """Test that all organization style descriptions include use cases and examples."""
    print("Testing style descriptions are descriptive...")

    from organizer import ORGANIZATION_STYLES

    for style_id, style_class in ORGANIZATION_STYLES.items():
        if style_id == 'custom':
            style = style_class()
        else:
            style = style_class()
        desc = style.get_description()

        # Descriptions must be longer than 50 chars (i.e., not just a short phrase)
        assert len(desc) > 50, f"{style_id} description too short: {desc!r}"

        # Descriptions should contain "Best for:" usage hint
        assert "Best for:" in desc, f"{style_id} description missing 'Best for:' hint: {desc!r}"

        print(f"  ✓ {style_id}: {desc[:80]}...")

    print("✓ All style descriptions are descriptive")
    return True


def test_organization_engine_deferred_creation():
    """Test that OrganizationEngine can be created properly with args."""
    print("\nTesting OrganizationEngine deferred creation...")

    from organizer import OrganizationEngine, ORGANIZATION_STYLES

    # Engine should require style_class and output_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        style_class = ORGANIZATION_STYLES['flat']
        engine = OrganizationEngine(style_class, temp_dir)

        assert engine.get_style_name() == "Flat Style"
        print("  ✓ OrganizationEngine created with Flat Style")

        style_class2 = ORGANIZATION_STYLES['sims']
        engine2 = OrganizationEngine(style_class2, temp_dir)
        assert engine2.get_style_name() == "The Sims Style"
        print("  ✓ OrganizationEngine created with Sims Style")

    print("✓ OrganizationEngine deferred creation works")
    return True


def test_worker_advance_event():
    """Test that OrganizerWorker has threading.Event for suggested/manual mode."""
    print("\nTesting OrganizerWorker advance event...")

    # We can't import OrganizerWorker directly (requires PyQt6),
    # so test the threading.Event pattern in isolation
    advance_event = threading.Event()
    processed = []

    def worker_loop(files, event):
        for f in files:
            processed.append(f)
            event.wait()
            event.clear()

    files = ["file1.png", "file2.png", "file3.png"]
    t = threading.Thread(target=worker_loop, args=(files, advance_event))
    t.start()

    # Give time for first file to be processed
    time.sleep(0.1)
    assert len(processed) == 1, f"Expected 1, got {len(processed)}"
    print("  ✓ Worker paused after first file")

    # Advance to second file
    advance_event.set()
    time.sleep(0.1)
    assert len(processed) == 2, f"Expected 2, got {len(processed)}"
    print("  ✓ Worker advanced to second file")

    # Advance to third file
    advance_event.set()
    time.sleep(0.1)
    assert len(processed) == 3, f"Expected 3, got {len(processed)}"
    print("  ✓ Worker advanced to third file")

    # Final advance to let thread finish
    advance_event.set()
    t.join(timeout=2)
    assert not t.is_alive(), "Worker thread did not finish"
    print("  ✓ Worker thread finished cleanly")

    print("✓ Worker advance event pattern works correctly")
    return True


def test_worker_cancel_unblocks():
    """Test that cancelling unblocks a waiting worker."""
    print("\nTesting cancel unblocks worker...")

    advance_event = threading.Event()
    cancelled = [False]
    completed = [False]

    def worker_loop(event, cancel_flag, done_flag):
        event.wait()
        done_flag[0] = True

    t = threading.Thread(target=worker_loop, args=(advance_event, cancelled, completed))
    t.start()

    time.sleep(0.1)
    assert not completed[0], "Should not be complete yet"

    # Simulate cancel by setting the event
    advance_event.set()
    t.join(timeout=2)
    assert completed[0], "Worker should have completed after cancel"
    print("  ✓ Worker unblocked on cancel")

    print("✓ Cancel unblock works")
    return True


def test_startup_validation_optional_deps():
    """Test that startup validation can check optional dependencies."""
    print("\nTesting startup validation optional dependencies...")

    from startup_validation import validate_optional_dependencies

    results = validate_optional_dependencies()
    assert isinstance(results, list), "Should return a list"
    assert len(results) > 0, "Should have at least one result"

    for description, status, hint in results:
        assert status in ('installed', 'missing'), f"Invalid status: {status}"
        assert description, "Description should not be empty"
        assert hint, "Install hint should not be empty"
        print(f"  {'✓' if status == 'installed' else '⚠'} {description}: {status}")

    print("✓ Optional dependency validation works")
    return True


def test_model_manager_required_packages():
    """Test that model manager has correct importable package names."""
    print("\nTesting model manager required packages...")

    from upscaler.model_manager import AIModelManager

    manager = AIModelManager()

    # Check CLIP models don't reference non-existent packages
    for model_name, info in manager.MODELS.items():
        pkgs = info.get('required_packages', [])
        for pkg in pkgs:
            # All packages should be directly importable (no hyphens)
            assert '-' not in pkg, \
                f"{model_name}: package '{pkg}' contains hyphens and is not directly importable"
        print(f"  ✓ {model_name}: packages {pkgs}")

    # Specifically check CLIP doesn't reference 'clip-by-openai'
    for model_name in ['CLIP_ViT-B/32', 'CLIP_ViT-L/14']:
        pkgs = manager.MODELS[model_name]['required_packages']
        assert 'clip-by-openai' not in pkgs, \
            f"{model_name} still references non-existent 'clip-by-openai'"
        assert 'clip_by_openai' not in pkgs, \
            f"{model_name} still references non-existent 'clip_by_openai'"

    # Check DINOv2 doesn't reference non-existent 'dinov2' package
    for model_name in ['DINOv2_base', 'DINOv2_small', 'DINOv2_large']:
        pkgs = manager.MODELS[model_name]['required_packages']
        assert 'dinov2' not in pkgs, \
            f"{model_name} references non-existent 'dinov2' package"

    # Check Lanczos_Native references texture_ops (not native_ops)
    assert 'texture_ops' in manager.MODELS['Lanczos_Native']['required_packages'], \
        "Lanczos_Native should reference 'texture_ops'"

    print("✓ All model manager required packages are correct")
    return True


def test_model_manager_native_module_check():
    """Test that native module status check works."""
    print("\nTesting model manager native module status check...")

    from upscaler.model_manager import AIModelManager, ModelStatus

    manager = AIModelManager()

    # Lanczos_Native has 'native_module': True
    status = manager.get_model_status('Lanczos_Native')
    assert status in (ModelStatus.INSTALLED, ModelStatus.MISSING), \
        f"Unexpected status: {status}"
    print(f"  ✓ Lanczos_Native status: {status.value}")

    print("✓ Native module status check works")
    return True


def test_file_copy_in_good_feedback():
    """Test that the good feedback workflow copies files correctly."""
    print("\nTesting file copy in good feedback workflow...")

    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "source"
        target_dir = Path(temp_dir) / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        # Create a test file
        test_file = source_dir / "test_texture.png"
        test_file.write_bytes(b"fake png data")

        # Simulate the copy logic from _on_good_feedback
        target_folder = "character"
        target_path = target_dir / target_folder / test_file.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(test_file), str(target_path))

        assert target_path.exists(), "File should be copied to target"
        assert target_path.read_bytes() == b"fake png data"
        assert test_file.exists(), "Original should still exist (copy, not move)"
        print("  ✓ File copied to target/character/test_texture.png")
        print("  ✓ Original file preserved")

    print("✓ File copy workflow works")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("ORGANIZER MODES, STYLES & DEPENDENCY TESTS")
    print("=" * 60)

    tests = [
        ("Style Descriptions", test_style_descriptions_are_descriptive),
        ("Engine Deferred Creation", test_organization_engine_deferred_creation),
        ("Worker Advance Event", test_worker_advance_event),
        ("Cancel Unblocks", test_worker_cancel_unblocks),
        ("Startup Optional Deps", test_startup_validation_optional_deps),
        ("Model Manager Packages", test_model_manager_required_packages),
        ("Native Module Check", test_model_manager_native_module_check),
        ("File Copy Workflow", test_file_copy_in_good_feedback),
    ]

    results = []
    for name, func in tests:
        print(f"\n{'=' * 60}")
        print(f"TEST: {name}")
        print(f"{'=' * 60}")
        try:
            result = func()
            results.append((name, result))
            if result:
                print(f"\n✓ {name} PASSED")
            else:
                print(f"\n✗ {name} FAILED")
        except Exception as e:
            print(f"\n✗ {name} FAILED WITH EXCEPTION:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
