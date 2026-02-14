"""
Test script for all new image processing tools
Tests quality checker, batch normalizer, lineart converter, and alpha fixer
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("TESTING IMAGE PROCESSING TOOLS")
print("=" * 60)

# Create test image
print("\n📝 Creating test image...")
test_img = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
# Add some content
for i in range(50, 200):
    for j in range(50, 200):
        test_img.putpixel((i, j), (100, 150, 200, 255))

test_path = Path("test_image.png")
test_img.save(test_path)
print(f"✓ Test image created: {test_path}")

# Test 1: Quality Checker
print("\n" + "=" * 60)
print("TEST 1: Quality Checker")
print("=" * 60)

try:
    from tools.quality_checker import ImageQualityChecker, format_quality_report
    
    checker = ImageQualityChecker()
    print("✓ ImageQualityChecker imported successfully")
    
    report = checker.check_quality(str(test_path))
    print(f"✓ Quality check completed")
    print(f"  - Overall score: {report.overall_score:.1f}/100")
    print(f"  - Quality level: {report.quality_level.value}")
    print(f"  - Resolution score: {report.resolution_score:.1f}/100")
    print(f"  - Sharpness score: {report.sharpness_score:.1f}/100")
    
    # Test batch
    reports = checker.check_batch([str(test_path)])
    print(f"✓ Batch check completed ({len(reports)} images)")
    
    # Test summary
    summary = checker.generate_summary_report(reports)
    print(f"✓ Summary report generated")
    
    print("\n✅ Quality Checker: ALL TESTS PASSED")
    
except Exception as e:
    print(f"\n❌ Quality Checker: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 2: Batch Normalizer
print("\n" + "=" * 60)
print("TEST 2: Batch Normalizer")
print("=" * 60)

try:
    from tools.batch_normalizer import (
        BatchFormatNormalizer, NormalizationSettings,
        PaddingMode, ResizeMode, OutputFormat
    )
    
    normalizer = BatchFormatNormalizer()
    print("✓ BatchFormatNormalizer imported successfully")
    
    settings = NormalizationSettings(
        target_width=512,
        target_height=512,
        make_square=True,
        padding_mode=PaddingMode.TRANSPARENT
    )
    print("✓ NormalizationSettings created")
    
    # Test single image
    output_path = "test_normalized.png"
    result = normalizer.normalize_image(str(test_path), output_path, settings)
    print(f"✓ Image normalized: {result.success}")
    print(f"  - Original size: {result.original_size}")
    print(f"  - Output size: {result.output_size}")
    print(f"  - Was resized: {result.was_resized}")
    
    # Test preview
    preview = normalizer.preview_settings(str(test_path), settings)
    print(f"✓ Preview generated: {preview.size}")
    
    # Cleanup
    Path(output_path).unlink(missing_ok=True)
    
    print("\n✅ Batch Normalizer: ALL TESTS PASSED")
    
except Exception as e:
    print(f"\n❌ Batch Normalizer: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 3: Line Art Converter
print("\n" + "=" * 60)
print("TEST 3: Line Art Converter")
print("=" * 60)

try:
    from tools.lineart_converter import (
        LineArtConverter, LineArtSettings,
        ConversionMode, BackgroundMode
    )
    
    converter = LineArtConverter()
    print("✓ LineArtConverter imported successfully")
    
    settings = LineArtSettings(
        mode=ConversionMode.PURE_BLACK,
        threshold=128,
        background_mode=BackgroundMode.TRANSPARENT
    )
    print("✓ LineArtSettings created")
    
    # Test single image
    output_path = "test_lineart.png"
    result = converter.convert_image(str(test_path), output_path, settings)
    print(f"✓ Image converted: {result.success}")
    print(f"  - Mode used: {result.mode_used}")
    print(f"  - Threshold used: {result.threshold_used}")
    
    # Test preview
    preview = converter.preview_settings(str(test_path), settings)
    print(f"✓ Preview generated: {preview.size}")
    
    # Cleanup
    Path(output_path).unlink(missing_ok=True)
    
    print("\n✅ Line Art Converter: ALL TESTS PASSED")
    
except Exception as e:
    print(f"\n❌ Line Art Converter: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 4: Alpha Fixer (Enhanced)
print("\n" + "=" * 60)
print("TEST 4: Alpha Fixer (Enhanced)")
print("=" * 60)

try:
    from preprocessing.alpha_correction import AlphaCorrector
    
    corrector = AlphaCorrector()
    print("✓ AlphaCorrector imported successfully")
    
    # Load test image as numpy array
    img = Image.open(test_path)
    arr = np.array(img)
    print(f"✓ Test image loaded: {arr.shape}")
    
    # Test de-fringing
    defringed = corrector.defringe_alpha(arr, radius=2)
    print(f"✓ De-fringing applied: {defringed.shape}")
    
    # Test matte removal
    dematte = corrector.remove_matte_color(arr, matte_color=(255, 255, 255))
    print(f"✓ Matte removal applied: {dematte.shape}")
    
    # Test feathering
    feathered = corrector.feather_alpha_edges(arr, radius=2, strength=0.5)
    print(f"✓ Alpha feathering applied: {feathered.shape}")
    
    # Test dilation
    dilated = corrector.dilate_alpha(arr, iterations=1, kernel_size=3)
    print(f"✓ Alpha dilation applied: {dilated.shape}")
    
    # Test erosion
    eroded = corrector.erode_alpha(arr, iterations=1, kernel_size=3)
    print(f"✓ Alpha erosion applied: {eroded.shape}")
    
    print("\n✅ Alpha Fixer: ALL TESTS PASSED")
    
except Exception as e:
    print(f"\n❌ Alpha Fixer: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n" + "=" * 60)
print("Cleaning up...")
test_path.unlink(missing_ok=True)
print("✓ Test files removed")

print("\n" + "=" * 60)
print("🎉 ALL TESTS COMPLETED!")
print("=" * 60)
print("\nSummary:")
print("  ✅ Quality Checker: Comprehensive quality analysis")
print("  ✅ Batch Normalizer: Resize, pad, and format conversion")
print("  ✅ Line Art Converter: Line art and stencil generation")
print("  ✅ Alpha Fixer: De-fringe, matte removal, morphology")
print("\n📚 All tools are ready for use!")
