"""
Example: Preprocessing Pipeline
Upscale and enhance textures
"""

from pathlib import Path
from PIL import Image
from src.preprocessing import PreprocessingPipeline

def main():
    # Initialize preprocessing pipeline
    print("Initializing preprocessing pipeline...")
    pipeline = PreprocessingPipeline(
        upscale_enabled=True,
        upscale_factor=4,
        upscale_method='bicubic',  # or 'realesrgan' for better quality
        sharpen_enabled=True,
        sharpen_method='unsharp',
        denoise_enabled=True,
        denoise_method='bilateral',
        normalize_colors=True,
        handle_alpha=True
    )
    
    # Input texture
    input_path = Path("path/to/small_texture.png")
    output_path = Path("output/enhanced_texture.png")
    
    if not input_path.exists():
        print(f"Texture not found: {input_path}")
        print("Please update the input_path variable")
        return
    
    # Process texture
    print(f"\nProcessing: {input_path.name}")
    result = pipeline.process(input_path, min_size_for_upscale=128)
    
    # Print info
    print(f"Original shape: {result['original_shape']}")
    print(f"Processed shape: {result['processed_shape']}")
    print(f"Upscaled: {result['upscaled']}")
    print(f"Has alpha: {result['has_alpha']}")
    
    # Save processed image
    output_path.parent.mkdir(exist_ok=True, parents=True)
    processed_img = Image.fromarray(result['image'])
    processed_img.save(output_path)
    print(f"\nSaved to: {output_path}")
    
    # Batch processing example
    print("\n--- Batch Processing ---")
    texture_folder = Path("path/to/textures")
    texture_paths = list(texture_folder.glob("*.png"))[:5]  # First 5
    
    if texture_paths:
        print(f"Processing {len(texture_paths)} textures...")
        results = pipeline.process_batch(texture_paths)
        
        for path, result in zip(texture_paths, results):
            if result:
                print(f"{path.name}: {result['original_shape']} -> "
                      f"{result['processed_shape']}")

if __name__ == '__main__':
    main()
