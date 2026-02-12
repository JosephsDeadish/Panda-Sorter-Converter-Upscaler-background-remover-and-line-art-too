"""
Example: Build Similarity Index
Build FAISS index and find similar textures
"""

from pathlib import Path
import glob
from src.vision_models import CLIPModel
from src.similarity import SimilaritySearch

def main():
    # Initialize models
    print("Loading CLIP model...")
    clip = CLIPModel(device='cpu')
    
    print("Initializing similarity search...")
    search = SimilaritySearch(embedding_dim=512, index_type='flat')
    
    # Find all textures
    texture_folder = Path("path/to/textures")
    texture_paths = list(texture_folder.glob("*.png"))
    
    if not texture_paths:
        print(f"No textures found in: {texture_folder}")
        print("Please update the texture_folder variable with a valid path")
        return
    
    # Generate embeddings and build index
    print(f"\nProcessing {len(texture_paths)} textures...")
    for i, texture_path in enumerate(texture_paths):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(texture_paths)}")
        
        try:
            # Generate embedding
            embedding = clip.encode_image(texture_path)
            
            # Add to index
            search.add_embedding(embedding, texture_path)
        except Exception as e:
            print(f"Failed to process {texture_path.name}: {e}")
    
    print(f"\nIndex built with {len(texture_paths)} textures")
    
    # Save index
    index_path = Path("texture_index")
    search.save(index_path)
    print(f"Index saved to: {index_path}")
    
    # Example: Find similar textures
    if texture_paths:
        query_texture = texture_paths[0]
        print(f"\nFinding textures similar to: {query_texture.name}")
        
        query_embedding = clip.encode_image(query_texture)
        similar = search.search(query_embedding, k=5)
        
        print("\nTop 5 similar textures:")
        for i, result in enumerate(similar, 1):
            print(f"{i}. {result['texture_path'].name} "
                  f"(similarity: {result['similarity']:.3f})")

if __name__ == '__main__':
    main()
