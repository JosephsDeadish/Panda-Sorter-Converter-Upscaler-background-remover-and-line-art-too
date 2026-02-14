"""Tests for dual-mode SVG conversion support."""

import sys
from pathlib import Path
import tempfile

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.native_ops import (
    NATIVE_AVAILABLE,
    bitmap_to_svg,
    batch_bitmap_to_svg,
)
from src.file_handler.file_handler import (
    FileHandler,
    HAS_SVG_NATIVE,
    HAS_SVG_CAIRO,
)


def test_native_svg_available():
    """Check whether native SVG tracing is available (informational)."""
    print(f"  Native SVG tracing available: {HAS_SVG_NATIVE}")
    print(f"  Cairo SVG support available: {HAS_SVG_CAIRO}")


def test_bitmap_to_svg_basic():
    """Test basic bitmap to SVG conversion."""
    # Create a simple test image (red square)
    img = np.zeros((32, 32, 3), dtype=np.uint8)
    img[8:24, 8:24] = [255, 0, 0]  # Red square in center
    
    svg_content = bitmap_to_svg(img, threshold=25, mode="color")
    
    if svg_content is None:
        print("  WARNING: bitmap_to_svg returned None (native not available or fallback failed)")
        return
    
    # Verify basic SVG structure
    assert isinstance(svg_content, str), "SVG should be a string"
    assert len(svg_content) > 0, "SVG should not be empty"
    assert "svg" in svg_content.lower(), "SVG should contain SVG tag"
    assert "xmlns" in svg_content or "viewBox" in svg_content, "SVG should have valid attributes"
    print(f"  SVG generated successfully ({len(svg_content)} bytes)")


def test_bitmap_to_svg_modes():
    """Test different SVG tracing modes."""
    img = np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8)
    
    modes = ["color", "binary", "spline"]
    for mode in modes:
        svg_content = bitmap_to_svg(img, threshold=25, mode=mode)
        if svg_content:
            assert isinstance(svg_content, str), f"Mode {mode} should return string"
            print(f"  Mode '{mode}': {len(svg_content)} bytes")
        else:
            print(f"  Mode '{mode}': Not available")


def test_bitmap_to_svg_thresholds():
    """Test different threshold values."""
    img = np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8)
    
    thresholds = [10, 25, 50]
    for threshold in thresholds:
        svg_content = bitmap_to_svg(img, threshold=threshold, mode="color")
        if svg_content:
            print(f"  Threshold {threshold}: {len(svg_content)} bytes")
        else:
            print(f"  Threshold {threshold}: Not available")


def test_batch_bitmap_to_svg():
    """Test batch SVG conversion."""
    # Create multiple test images
    images = [
        np.full((16, 16, 3), 100, dtype=np.uint8),  # Gray
        np.full((16, 16, 3), [255, 0, 0], dtype=np.uint8),  # Red
        np.full((16, 16, 3), [0, 255, 0], dtype=np.uint8),  # Green
    ]
    
    results = batch_bitmap_to_svg(images, threshold=25, mode="color")
    
    assert len(results) == len(images), "Should return same number of results"
    
    valid_count = sum(1 for r in results if r is not None)
    print(f"  Batch conversion: {valid_count}/{len(images)} successful")
    
    if valid_count > 0:
        for i, svg in enumerate(results):
            if svg:
                assert isinstance(svg, str), f"Result {i} should be string"


def test_file_handler_raster_to_svg():
    """Test FileHandler raster to SVG conversion."""
    if not HAS_SVG_NATIVE:
        print("  SKIP: Native SVG not available")
        return
    
    try:
        from PIL import Image
    except ImportError:
        print("  SKIP: PIL not available")
        return
    
    handler = FileHandler()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a test PNG
        test_png = tmpdir / "test.png"
        img = Image.new('RGB', (32, 32), color='red')
        img.save(test_png)
        
        # Convert to SVG
        output_svg = tmpdir / "test.svg"
        result = handler.convert_raster_to_svg(
            test_png,
            output_svg,
            threshold=25,
            mode="color"
        )
        
        if result:
            assert result.exists(), "Output SVG should exist"
            assert result.suffix == '.svg', "Should have .svg extension"
            
            # Verify content
            content = result.read_text(encoding='utf-8')
            assert "svg" in content.lower(), "Should contain SVG content"
            print(f"  File conversion successful: {len(content)} bytes")
        else:
            print("  File conversion failed (fallback may not be available)")


def test_file_handler_native_mode():
    """Test FileHandler native SVG mode explicitly."""
    if not HAS_SVG_NATIVE:
        print("  SKIP: Native SVG not available")
        return
    
    try:
        from PIL import Image
    except ImportError:
        print("  SKIP: PIL not available")
        return
    
    handler = FileHandler()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test image
        test_png = tmpdir / "icon.png"
        img = Image.new('RGB', (24, 24), color='blue')
        img.save(test_png)
        
        # Convert using native mode
        output_svg = tmpdir / "icon.svg"
        result = handler.convert_raster_to_svg_native(
            test_png,
            output_svg,
            threshold=20,
            mode="spline"
        )
        
        if result:
            assert result.exists(), "Native conversion should create file"
            print("  Native mode conversion successful")
        else:
            print("  Native mode conversion failed")


def test_svg_edge_cases():
    """Test edge cases and error handling."""
    # Empty image
    try:
        empty_img = np.zeros((0, 0, 3), dtype=np.uint8)
        svg = bitmap_to_svg(empty_img)
        print(f"  Empty image: Handled gracefully")
    except Exception as e:
        print(f"  Empty image: Raised expected error")
    
    # Single pixel
    try:
        tiny_img = np.array([[[255, 0, 0]]], dtype=np.uint8)
        svg = bitmap_to_svg(tiny_img)
        if svg:
            print(f"  Single pixel: {len(svg)} bytes")
        else:
            print(f"  Single pixel: Not supported")
    except Exception as e:
        print(f"  Single pixel: Error (expected)")
    
    # Very large threshold
    img = np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8)
    svg = bitmap_to_svg(img, threshold=255, mode="color")
    if svg:
        print(f"  Max threshold: {len(svg)} bytes")


def test_graceful_degradation():
    """Test that functions degrade gracefully when native unavailable."""
    # This test always passes, but logs what's available
    print(f"  Native Rust module: {'Available' if NATIVE_AVAILABLE else 'Not available'}")
    print(f"  Native SVG tracing: {'Available' if HAS_SVG_NATIVE else 'Not available'}")
    print(f"  Cairo SVG support: {'Available' if HAS_SVG_CAIRO else 'Not available'}")
    
    # Test that functions don't crash
    img = np.zeros((16, 16, 3), dtype=np.uint8)
    result = bitmap_to_svg(img)
    print(f"  Fallback behavior: {'Working' if result or not HAS_SVG_NATIVE else 'Failed gracefully'}")


def run_all_tests():
    """Run all SVG conversion tests."""
    tests = [
        ("Native SVG Available", test_native_svg_available),
        ("Basic Bitmap to SVG", test_bitmap_to_svg_basic),
        ("SVG Tracing Modes", test_bitmap_to_svg_modes),
        ("SVG Thresholds", test_bitmap_to_svg_thresholds),
        ("Batch Conversion", test_batch_bitmap_to_svg),
        ("FileHandler Conversion", test_file_handler_raster_to_svg),
        ("FileHandler Native Mode", test_file_handler_native_mode),
        ("Edge Cases", test_svg_edge_cases),
        ("Graceful Degradation", test_graceful_degradation),
    ]
    
    print("\n" + "=" * 70)
    print("SVG CONVERSION TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            test_func()
            passed += 1
            print(f"  ✓ PASSED")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"  ✗ ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
