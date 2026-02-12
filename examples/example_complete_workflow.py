"""
Example: Complete Workflow
Full pipeline: preprocessing, classification, similarity search
"""

from pathlib import Path
from src.advanced_analyzer import AdvancedTextureAnalyzer

def main():
    # Initialize analyzer with all features
    print("Initializing advanced texture analyzer...")
    analyzer = AdvancedTextureAnalyzer(
        use_preprocessing=True,
        use_clip=True,
        use_dinov2=False,  # Optional, slower
        use_faiss=True,
        device='cpu'  # Use 'cuda' for GPU
    )
    
    # Find textures
    texture_folder = Path("path/to/textures")
    texture_paths = list(texture_folder.glob("*.png"))
    
    if not texture_paths:
        print(f"No textures found in: {texture_folder}")
        print("Please update the texture_folder variable")
        return
    
    print(f"\nFound {len(texture_paths)} textures")
    
    # Batch analyze and build index
    print("\nAnalyzing textures and building similarity index...")
    results = analyzer.batch_analyze(
        texture_paths,
        preprocess=True,
        add_to_index=True
    )
    
    print(f"Analyzed {len(results)} textures")
    
    # Example 1: Classify a texture
    if texture_paths:
        test_texture = texture_paths[0]
        print(f"\n--- Classification Example ---")
        print(f"Classifying: {test_texture.name}")
        
        categories = ["ui", "character", "environment", "weapon"]
        predictions = analyzer.classify_texture(test_texture, categories)
        
        print("Predictions:")
        for pred in predictions[:3]:
            print(f"  {pred['category']}: {pred['probability']:.2%}")
    
    # Example 2: Find similar textures
    if texture_paths:
        query_texture = texture_paths[0]
        print(f"\n--- Similarity Search Example ---")
        print(f"Finding textures similar to: {query_texture.name}")
        
        similar = analyzer.find_similar_textures(query_texture, k=5)
        
        print("Similar textures:")
        for result in similar:
            print(f"  {result['texture_path'].name} "
                  f"(similarity: {result['similarity']:.3f})")
    
    # Example 3: Detect duplicates
    print(f"\n--- Duplicate Detection Example ---")
    duplicates = analyzer.detect_duplicates(threshold=0.99)
    
    print(f"Found {len(duplicates)} duplicate groups")
    for i, group in enumerate(duplicates[:3], 1):
        print(f"\nGroup {i}:")
        for path in group:
            print(f"  - {path.name}")
    
    # Save index for later use
    index_path = Path("saved_index")
    analyzer.save_index(index_path)
    print(f"\n\nIndex saved to: {index_path}")
    print("You can load it later with: analyzer.load_index(index_path)")

if __name__ == '__main__':
    main()
