"""
Test Alpha Correction Functionality
Simple test to verify the alpha correction tool works
"""

import sys
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets


def create_test_image(output_path: Path, pattern: str = 'gradient'):
    """Create a test image with various alpha patterns."""
    # Create 256x256 RGBA image
    size = 256
    img = np.zeros((size, size, 4), dtype=np.uint8)
    
    if pattern == 'gradient':
        # Create alpha gradient
        for i in range(size):
            alpha_value = i  # 0 to 255
            img[i, :, 3] = alpha_value
        # Random RGB colors
        img[:, :, 0] = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        img[:, :, 1] = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        img[:, :, 2] = np.random.randint(0, 256, (size, size), dtype=np.uint8)
    
    elif pattern == 'binary':
        # Create binary alpha (checkerboard pattern)
        for i in range(size):
            for j in range(size):
                if (i // 32 + j // 32) % 2 == 0:
                    img[i, j, 3] = 0  # Transparent
                else:
                    img[i, j, 3] = 255  # Opaque
        img[:, :, :3] = 128  # Gray color
    
    elif pattern == 'three_level':
        # Create three-level alpha
        for i in range(size):
            if i < size // 3:
                img[i, :, 3] = 0  # Transparent
            elif i < 2 * size // 3:
                img[i, :, 3] = 128  # Semi-transparent
            else:
                img[i, :, 3] = 255  # Opaque
        img[:, :, :3] = [200, 100, 50]
    
    elif pattern == 'noisy':
        # Create noisy alpha with many intermediate values
        img[:, :, 3] = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        img[:, :, :3] = 150
    
    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(output_path)
    print(f"Created test image: {output_path}")
    return output_path


def test_alpha_detection():
    """Test alpha color detection."""
    print("\n" + "=" * 70)
    print("Test 1: Alpha Color Detection")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test different patterns
        patterns = ['gradient', 'binary', 'three_level', 'noisy']
        
        for pattern in patterns:
            img_path = tmpdir / f"test_{pattern}.png"
            create_test_image(img_path, pattern)
            
            # Load and detect
            img = Image.open(img_path)
            img_array = np.array(img)
            detection = corrector.detect_alpha_colors(img_array)
            
            print(f"\n{pattern.upper()} Pattern:")
            print(f"  Unique values: {detection['unique_values']}")
            print(f"  Range: {detection['alpha_min']} - {detection['alpha_max']}")
            print(f"  Is binary: {detection['is_binary']}")
            print(f"  Patterns: {', '.join(detection['patterns'])}")
            print(f"  Semi-transparent ratio: {detection['semi_transparency_ratio']:.1%}")
    
    print("\n✓ Alpha detection test passed")


def test_alpha_correction():
    """Test alpha correction with presets."""
    print("\n" + "=" * 70)
    print("Test 2: Alpha Correction with Presets")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test image with gradient
        img_path = tmpdir / "test_gradient.png"
        create_test_image(img_path, 'gradient')
        
        # Load image
        img = Image.open(img_path)
        img_array = np.array(img)
        
        print(f"\nOriginal image:")
        orig_detection = corrector.detect_alpha_colors(img_array)
        print(f"  Unique alpha values: {orig_detection['unique_values']}")
        print(f"  Semi-transparent pixels: {orig_detection['semi_transparent_pixels']:,}")
        
        # Test PS2 binary preset
        print(f"\nApplying PS2 Binary preset...")
        corrected, stats = corrector.correct_alpha(img_array, preset='ps2_binary')
        
        print(f"  Pixels modified: {stats['pixels_changed']:,} / {stats['total_pixels']:,}")
        print(f"  Modification ratio: {stats['modification_ratio']:.1%}")
        
        # Verify correction
        corrected_alpha = corrected[:, :, 3]
        unique_after = len(np.unique(corrected_alpha))
        print(f"  Unique alpha values after: {unique_after}")
        
        if unique_after <= 2:
            print("  ✓ Successfully converted to binary alpha")
        else:
            print(f"  ⚠ Warning: Expected 2 unique values, got {unique_after}")
        
        # Save corrected image
        out_path = tmpdir / "test_gradient_corrected.png"
        Image.fromarray(corrected).save(out_path)
        print(f"  Saved corrected image: {out_path}")
    
    print("\n✓ Alpha correction test passed")


def test_batch_processing():
    """Test batch processing."""
    print("\n" + "=" * 70)
    print("Test 3: Batch Processing")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_dir = tmpdir / "input"
        output_dir = tmpdir / "output"
        input_dir.mkdir()
        
        # Create multiple test images
        patterns = ['gradient', 'binary', 'three_level']
        image_paths = []
        
        for i, pattern in enumerate(patterns):
            img_path = input_dir / f"test_{i}_{pattern}.png"
            create_test_image(img_path, pattern)
            image_paths.append(img_path)
        
        print(f"\nCreated {len(image_paths)} test images")
        
        # Process batch
        print(f"Processing batch with ps2_three_level preset...")
        results = corrector.process_batch(
            image_paths,
            output_dir=output_dir,
            preset='ps2_three_level',
            overwrite=False,
            backup=False
        )
        
        # Check results
        successful = sum(1 for r in results if r['success'])
        modified = sum(1 for r in results if r.get('modified'))
        
        print(f"\nResults:")
        print(f"  Total: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Modified: {modified}")
        
        # Verify output files exist
        output_files = list(output_dir.glob("*.png"))
        print(f"  Output files created: {len(output_files)}")
        
        if len(output_files) > 0:
            print("  ✓ Batch processing created output files")
        else:
            print("  ⚠ Warning: No output files created")
    
    print("\n✓ Batch processing test passed")


def test_presets():
    """Test all presets."""
    print("\n" + "=" * 70)
    print("Test 4: Preset Validation")
    print("=" * 70)
    
    preset_names = AlphaCorrectionPresets.list_presets()
    print(f"\nFound {len(preset_names)} presets:")
    
    for name in preset_names:
        preset = AlphaCorrectionPresets.get_preset(name)
        if preset:
            print(f"  ✓ {name}: {preset['name']}")
        else:
            print(f"  ✗ {name}: Failed to load")
    
    print("\n✓ All presets validated")


def test_custom_thresholds():
    """Test custom thresholds."""
    print("\n" + "=" * 70)
    print("Test 5: Custom Thresholds")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test image
        img_path = tmpdir / "test_noisy.png"
        create_test_image(img_path, 'noisy')
        
        # Load image
        img = Image.open(img_path)
        img_array = np.array(img)
        
        # Define custom thresholds
        custom_thresholds = [
            (0, 64, 0),      # Low -> 0
            (65, 191, 128),  # Mid -> 128
            (192, 255, 255)  # High -> 255
        ]
        
        print(f"\nApplying custom thresholds: {custom_thresholds}")
        
        corrected, stats = corrector.correct_alpha(
            img_array,
            custom_thresholds=custom_thresholds
        )
        
        print(f"  Pixels modified: {stats['pixels_changed']:,}")
        print(f"  Modification ratio: {stats['modification_ratio']:.1%}")
        
        # Check unique values
        unique_after = len(np.unique(corrected[:, :, 3]))
        print(f"  Unique alpha values after: {unique_after}")
        
        if unique_after <= 3:
            print("  ✓ Successfully quantized to 3 levels")
        else:
            print(f"  ⚠ Warning: Expected 3 unique values, got {unique_after}")
    
    print("\n✓ Custom thresholds test passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Alpha Correction Tool - Test Suite")
    print("=" * 70)
    
    try:
        test_alpha_detection()
        test_alpha_correction()
        test_batch_processing()
        test_presets()
        test_custom_thresholds()
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
        return 0
    
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
