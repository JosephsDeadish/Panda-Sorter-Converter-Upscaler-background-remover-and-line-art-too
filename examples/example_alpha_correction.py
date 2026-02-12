"""
Example: Alpha Color Detection and Correction
Demonstrates batch alpha correction with PS2 presets
Author: Dead On The Inside / JosephsDeadish
"""

from pathlib import Path
import numpy as np
from PIL import Image
from src.preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets


def example_single_image():
    """Example: Correct alpha in a single image."""
    print("=" * 70)
    print("Example 1: Single Image Alpha Correction")
    print("=" * 70)
    
    # Initialize corrector
    corrector = AlphaCorrector()
    
    # Process an image with PS2 binary preset
    input_path = Path("path/to/texture.png")
    
    if not input_path.exists():
        print(f"\nImage not found: {input_path}")
        print("Please update the input_path variable with a real image path")
        return
    
    print(f"\nProcessing: {input_path}")
    
    # First, analyze the image to see what we're working with
    img = Image.open(input_path)
    if img.mode == 'RGBA':
        img_array = np.array(img)
        detection = corrector.detect_alpha_colors(img_array)
        
        print("\n--- Alpha Analysis ---")
        print(f"Unique alpha values: {detection['unique_values']}")
        print(f"Dominant values: {detection['dominant_values'][:5]}")
        print(f"Patterns detected: {', '.join(detection['patterns'])}")
        print(f"Is binary: {detection['is_binary']}")
    
    # Correct with PS2 binary preset
    result = corrector.process_image(
        input_path,
        preset='ps2_binary',
        overwrite=False
    )
    
    if result['success'] and result['modified']:
        print(f"\n✓ Alpha corrected successfully!")
        print(f"Output saved to: {result['output_path']}")
        print(f"Pixels modified: {result['correction']['pixels_changed']:,}")
    elif result['success']:
        print(f"\n✓ No correction needed: {result.get('reason', '')}")
    else:
        print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")


def example_batch_processing():
    """Example: Batch process multiple images."""
    print("\n" + "=" * 70)
    print("Example 2: Batch Alpha Correction")
    print("=" * 70)
    
    # Initialize corrector
    corrector = AlphaCorrector()
    
    # Find images to process
    input_dir = Path("path/to/textures")
    output_dir = Path("path/to/output")
    
    if not input_dir.exists():
        print(f"\nDirectory not found: {input_dir}")
        print("Please update the input_dir variable with a real directory path")
        return
    
    # Find all PNG images
    image_paths = list(input_dir.glob("*.png"))
    
    if not image_paths:
        print(f"No PNG images found in {input_dir}")
        return
    
    print(f"\nFound {len(image_paths)} images")
    print(f"Using preset: ps2_three_level")
    
    # Progress callback
    def progress(current, total):
        print(f"Progress: {current}/{total} ({100*current//total}%)", end='\r')
    
    # Process batch
    results = corrector.process_batch(
        image_paths,
        output_dir=output_dir,
        preset='ps2_three_level',
        preserve_structure=False,
        progress_callback=progress
    )
    
    print()  # New line after progress
    
    # Display summary
    successful = sum(1 for r in results if r['success'])
    modified = sum(1 for r in results if r.get('modified'))
    
    print(f"\n✓ Batch processing complete")
    print(f"  Successfully processed: {successful}/{len(results)}")
    print(f"  Modified: {modified}")
    print(f"  Output directory: {output_dir}")


def example_custom_thresholds():
    """Example: Use custom alpha thresholds."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Alpha Thresholds")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    input_path = Path("path/to/texture.png")
    
    if not input_path.exists():
        print(f"\nImage not found: {input_path}")
        return
    
    # Define custom thresholds
    # Format: (min_alpha, max_alpha, target_alpha)
    # Use None as target to preserve gradient in that range
    custom_thresholds = [
        (0, 50, 0),        # Very transparent -> fully transparent
        (51, 200, None),   # Mid-range -> preserve gradient
        (201, 255, 255)    # Nearly opaque -> fully opaque
    ]
    
    print(f"\nProcessing with custom thresholds: {custom_thresholds}")
    
    # Load image
    img = Image.open(input_path).convert('RGBA')
    img_array = np.array(img)
    
    # Apply correction
    corrected, stats = corrector.correct_alpha(
        img_array,
        custom_thresholds=custom_thresholds
    )
    
    if stats['modified']:
        # Save result
        output_path = input_path.with_stem(f"{input_path.stem}_custom")
        corrected_img = Image.fromarray(corrected)
        corrected_img.save(output_path)
        
        print(f"\n✓ Correction applied")
        print(f"Pixels modified: {stats['pixels_changed']:,}")
        print(f"Output: {output_path}")
    else:
        print("\n✓ No changes needed")


def example_analyze_alpha_distribution():
    """Example: Analyze alpha channel distribution."""
    print("\n" + "=" * 70)
    print("Example 4: Analyze Alpha Distribution")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    # Analyze multiple images
    texture_dir = Path("path/to/textures")
    
    if not texture_dir.exists():
        print(f"\nDirectory not found: {texture_dir}")
        return
    
    image_paths = list(texture_dir.glob("*.png"))[:10]  # First 10
    
    if not image_paths:
        print(f"No PNG images found in {texture_dir}")
        return
    
    print(f"\nAnalyzing {len(image_paths)} images...\n")
    
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            if img.mode != 'RGBA':
                print(f"{img_path.name}: No alpha channel")
                continue
            
            img_array = np.array(img)
            detection = corrector.detect_alpha_colors(img_array)
            
            print(f"\n{img_path.name}:")
            print(f"  Unique values: {detection['unique_values']}")
            print(f"  Range: {detection['alpha_min']} - {detection['alpha_max']}")
            print(f"  Patterns: {', '.join(detection['patterns']) if detection['patterns'] else 'None'}")
            
            # Show dominant alpha values
            if detection['dominant_values']:
                print(f"  Top alpha values:")
                for value, count in detection['dominant_values'][:3]:
                    percentage = 100 * count / (img_array.shape[0] * img_array.shape[1])
                    print(f"    {value}: {percentage:.1f}%")
        
        except Exception as e:
            print(f"Error processing {img_path}: {e}")


def example_presets_comparison():
    """Example: Compare different presets."""
    print("\n" + "=" * 70)
    print("Example 5: Compare Alpha Correction Presets")
    print("=" * 70)
    
    corrector = AlphaCorrector()
    
    input_path = Path("path/to/texture.png")
    
    if not input_path.exists():
        print(f"\nImage not found: {input_path}")
        return
    
    # Load image
    img = Image.open(input_path).convert('RGBA')
    img_array = np.array(img)
    
    # Test different presets
    presets = [
        'ps2_binary',
        'ps2_three_level',
        'ps2_smooth',
        'clean_edges'
    ]
    
    print(f"\nComparing presets on: {input_path.name}\n")
    
    for preset_name in presets:
        corrected, stats = corrector.correct_alpha(img_array.copy(), preset=preset_name)
        
        preset = AlphaCorrectionPresets.get_preset(preset_name)
        print(f"{preset['name']}:")
        print(f"  {preset['description']}")
        print(f"  Modified pixels: {stats['pixels_changed']:,} ({stats['modification_ratio']:.1%})")
        
        # Save comparison image
        output_path = input_path.with_stem(f"{input_path.stem}_{preset_name}")
        Image.fromarray(corrected).save(output_path)
        print(f"  Saved to: {output_path.name}")
        print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Alpha Color Detection and Correction Examples")
    print("=" * 70)
    print("\nNote: Update the file paths in each example before running")
    print()
    
    # Uncomment the examples you want to run:
    
    # example_single_image()
    # example_batch_processing()
    # example_custom_thresholds()
    # example_analyze_alpha_distribution()
    # example_presets_comparison()
    
    print("\n" + "=" * 70)
    print("List of Available Presets:")
    print("=" * 70)
    
    presets = {
        'ps2_binary': AlphaCorrectionPresets.PS2_BINARY,
        'ps2_three_level': AlphaCorrectionPresets.PS2_THREE_LEVEL,
        'ps2_ui': AlphaCorrectionPresets.PS2_UI,
        'ps2_smooth': AlphaCorrectionPresets.PS2_SMOOTH,
        'generic_binary': AlphaCorrectionPresets.GENERIC_BINARY,
        'clean_edges': AlphaCorrectionPresets.CLEAN_EDGES,
    }
    
    for name, preset in presets.items():
        print(f"\n{name}:")
        print(f"  {preset['description']}")


if __name__ == '__main__':
    main()
