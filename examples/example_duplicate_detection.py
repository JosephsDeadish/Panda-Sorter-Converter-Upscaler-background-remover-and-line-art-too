"""
Example: Detect Duplicates
Find duplicate and variant textures
"""

from pathlib import Path
from src.vision_models import CLIPModel
from src.similarity import SimilaritySearch, DuplicateDetector

def main():
    # Initialize models
    print("Loading CLIP model...")
    clip = CLIPModel(device='cpu')
    
    print("Initializing similarity search...")
    search = SimilaritySearch(embedding_dim=512)
    
    # Find all textures
    texture_folder = Path("path/to/textures")
    texture_paths = list(texture_folder.glob("*.png"))
    
    if not texture_paths:
        print(f"No textures found in: {texture_folder}")
        print("Please update the texture_folder variable")
        return
    
    # Build index
    print(f"\nProcessing {len(texture_paths)} textures...")
    for i, texture_path in enumerate(texture_paths):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(texture_paths)}")
        
        try:
            embedding = clip.encode_image(texture_path)
            search.add_embedding(embedding, texture_path)
        except Exception as e:
            print(f"Failed: {texture_path.name}: {e}")
    
    # Find duplicates
    print("\nDetecting duplicates...")
    detector = DuplicateDetector(search)
    
    # Find exact duplicates (99% similar)
    exact_duplicates = detector.find_exact_duplicates(threshold=0.99)
    print(f"\nFound {len(exact_duplicates)} exact duplicate groups:")
    for i, group in enumerate(exact_duplicates[:5], 1):  # Show first 5
        print(f"\nGroup {i}:")
        for path in group:
            print(f"  - {path.name}")
    
    # Find variants (85-99% similar)
    if texture_paths:
        query_texture = texture_paths[0]
        print(f"\n\nFinding variants of: {query_texture.name}")
        variants = detector.find_variants(
            query_texture,
            min_similarity=0.85,
            max_similarity=0.99
        )
        
        print(f"Found {len(variants)} variants:")
        for variant in variants[:10]:  # Show first 10
            print(f"  - {variant['texture_path'].name} "
                  f"(similarity: {variant['similarity']:.3f})")
    
    # Group by similarity
    print("\n\nGrouping textures by similarity...")
    groups = detector.group_by_similarity(threshold=0.9)
    print(f"Created {len(groups)} similarity groups")
    
    for i, group in enumerate(groups[:3], 1):  # Show first 3 groups
        print(f"\nGroup {i} ({len(group)} textures):")
        for item in group[:5]:  # Show first 5 in each group
            print(f"  - {item['texture_path'].name}")

if __name__ == '__main__':
    main()
