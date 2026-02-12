"""
Example: Basic CLIP Classification
Classify textures using CLIP model
"""

from pathlib import Path
from src.vision_models import CLIPModel

def main():
    # Initialize CLIP model
    print("Loading CLIP model...")
    clip = CLIPModel(device='cpu')  # Use 'cuda' for GPU
    
    # Categories for PS2 textures
    categories = [
        "ui",
        "character",
        "environment",
        "weapon",
        "vehicle",
        "metal",
        "wood",
        "stone",
        "fabric",
        "grass",
        "water",
        "sky"
    ]
    
    # Example texture path
    texture_path = Path("path/to/texture.png")
    
    if not texture_path.exists():
        print(f"Texture not found: {texture_path}")
        print("Please update the texture_path variable with a valid path")
        return
    
    # Classify texture
    print(f"\nClassifying: {texture_path.name}")
    predictions = clip.classify_texture(texture_path, categories)
    
    # Print top 5 predictions
    print("\nTop 5 predictions:")
    for i, pred in enumerate(predictions[:5], 1):
        print(f"{i}. {pred['category']}: {pred['probability']:.2%} "
              f"(similarity: {pred['similarity']:.3f})")

if __name__ == '__main__':
    main()
