# Advanced Vision Models and Preprocessing

**Author:** Dead On The Inside / JosephsDeadish  
**Version:** 1.0.0

## Overview

This module provides advanced computer vision capabilities for PS2 texture analysis, including:

1. **Vision Models** - CLIP, DINOv2, ViT, EfficientNet, SAM
2. **Preprocessing Pipeline** - Upscaling, filtering, normalization
3. **Similarity Search** - FAISS-based vector database
4. **Duplicate Detection** - Find duplicates and variants

## Features

### Vision Models

#### CLIP (Contrastive Language-Image Pre-training)
- **Image-to-text comparison**: Compare textures to text descriptions
- **Image-to-image similarity**: Compare textures to each other
- **Zero-shot classification**: Classify without training
- **Strong on low-res textures**: Handles PS2 resolution well

```python
from src.vision_models import CLIPModel

clip = CLIPModel()
embedding = clip.encode_image("texture.png")
predictions = clip.classify_texture(
    "texture.png",
    categories=["metal", "wood", "stone", "fabric"]
)
```

#### DINOv2
- **Visual similarity**: Excellent for clustering
- **No text needed**: Pure visual features
- **Dense features**: Rich representation

```python
from src.vision_models import DINOv2Model

dinov2 = DINOv2Model()
embedding = dinov2.encode_image("texture.png")
```

#### Vision Transformer (ViT)
- **Transformer architecture**: State-of-the-art classification
- **Fine-tunable**: Can be trained on custom data

#### EfficientNet/ResNet
- **Efficient**: Fast inference
- **Customizable**: Easy to fine-tune

#### Segment Anything Model (SAM)
- **Object segmentation**: Separate UI elements
- **Zero-shot**: Works without training
- **Versatile**: Handles various object types

### Preprocessing Pipeline

Complete PS2 texture preprocessing:

```python
from src.preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    upscale_enabled=True,
    upscale_factor=4,
    upscale_method='bicubic',  # or 'realesrgan'
    sharpen_enabled=True,
    denoise_enabled=True,
    normalize_colors=True
)

result = pipeline.process("small_texture.png")
processed_image = result['image']
```

#### Upscaling
- **Bicubic**: Fast, good quality
- **ESRGAN**: Best quality, slower
- **Real-ESRGAN**: Optimized for retro textures

#### Filters
- **Sharpening**: Laplacian, Unsharp mask
- **Denoising**: Non-local means, Bilateral
- **Edge detection**: Canny, Sobel
- **Color normalization**: Fix PS2 gamma, reduce banding

#### Alpha Channel Handling
- Separate alpha masks
- Detect UI transparency patterns
- Remove backgrounds
- Analyze silhouettes

### Similarity Search

FAISS-based vector database for fast similarity search:

```python
from src.similarity import SimilaritySearch

# Create index
search = SimilaritySearch(embedding_dim=512, index_type='flat')

# Add embeddings
search.add_embedding(embedding, texture_path)

# Find similar textures
similar = search.search(query_embedding, k=10)

# Find duplicates
duplicates = search.find_duplicates(threshold=0.99)

# Cluster similar textures
clusters = search.cluster_similar(threshold=0.9)
```

### Duplicate Detection

Detect exact duplicates and variants:

```python
from src.similarity import DuplicateDetector

detector = DuplicateDetector(similarity_search)

# Find exact duplicates
duplicates = detector.find_exact_duplicates(threshold=0.99)

# Find color variants
variants = detector.find_variants(texture_path, min_similarity=0.85)

# Group by similarity
groups = detector.group_by_similarity(threshold=0.9)
```

## Complete Workflow

```python
from src.advanced_analyzer import AdvancedTextureAnalyzer

# Initialize analyzer
analyzer = AdvancedTextureAnalyzer(
    use_preprocessing=True,
    use_clip=True,
    use_faiss=True
)

# Analyze single texture
result = analyzer.analyze_texture("texture.png")

# Batch analyze and build index
texture_paths = [Path(p) for p in glob.glob("textures/*.png")]
analyzer.batch_analyze(texture_paths, add_to_index=True)

# Classify texture
predictions = analyzer.classify_texture(
    "texture.png",
    categories=["ui", "character", "environment", "weapon"]
)

# Find similar textures
similar = analyzer.find_similar_textures("texture.png", k=10)

# Detect duplicates
duplicates = analyzer.detect_duplicates(threshold=0.99)

# Save index for later use
analyzer.save_index(Path("texture_index"))
```

## Installation

### Required Dependencies

```bash
pip install torch torchvision transformers timm open-clip-torch
pip install faiss-cpu chromadb annoy
pip install basicsr realesrgan
pip install opencv-python scikit-image
```

### GPU Support (Optional)

For faster processing with CUDA:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install faiss-gpu
```

## Performance

### Memory Usage
- **CLIP**: ~400 MB
- **DINOv2**: ~350 MB
- **ViT**: ~300 MB
- **EfficientNet**: ~50-200 MB
- **FAISS Index**: ~2 KB per embedding

### Speed (CPU)
- **CLIP encoding**: ~100ms per image
- **Preprocessing**: ~50-200ms per image
- **FAISS search**: <1ms for 10K embeddings

### Speed (GPU)
- **CLIP encoding**: ~20ms per image
- **Batch processing**: ~5ms per image

## Configuration

### Preprocessing Config

```python
{
    'upscale_enabled': True,
    'upscale_factor': 4,
    'upscale_method': 'bicubic',
    'sharpen_enabled': True,
    'sharpen_method': 'unsharp',
    'denoise_enabled': False,
    'normalize_colors': True,
    'handle_alpha': True,
    'detect_edges': False
}
```

### CLIP Config

```python
{
    'model_name': 'openai/clip-vit-base-patch32',
    'device': 'cuda',  # or 'cpu'
    'use_open_clip': False
}
```

### FAISS Config

```python
{
    'embedding_dim': 512,
    'index_type': 'flat',  # 'flat', 'ivf', 'hnsw'
    'metric': 'cosine',
    'use_gpu': True
}
```

## Use Cases

### 1. Auto-classify Textures

```python
# Classify all textures into categories
for texture_path in texture_paths:
    predictions = analyzer.classify_texture(
        texture_path,
        categories=["ui", "character", "environment", "weapon"]
    )
    print(f"{texture_path.name}: {predictions[0]['category']}")
```

### 2. Find Duplicate Textures

```python
# Build index
analyzer.batch_analyze(texture_paths, add_to_index=True)

# Find duplicates
duplicates = analyzer.detect_duplicates(threshold=0.99)
for group in duplicates:
    print(f"Duplicate group: {[p.name for p in group]}")
```

### 3. Organize by Similarity

```python
# Cluster similar textures
from src.similarity import DuplicateDetector
detector = DuplicateDetector(analyzer.similarity_search)
groups = detector.group_by_similarity(threshold=0.9)

# Save to folders
for i, group in enumerate(groups):
    folder = Path(f"cluster_{i}")
    folder.mkdir(exist_ok=True)
    for item in group:
        # Copy to cluster folder
        ...
```

### 4. Find Texture Variants

```python
# Find color swaps and brightness variants
variants = detector.find_variants(
    texture_path,
    min_similarity=0.85,
    max_similarity=0.99
)
```

## Troubleshooting

### Out of Memory

Reduce batch size or use CPU:

```python
analyzer = AdvancedTextureAnalyzer(device='cpu')
```

### Slow Performance

- Use GPU acceleration
- Reduce upscaling factor
- Use 'flat' FAISS index for small datasets
- Disable preprocessing if not needed

### Model Not Loading

Check dependencies:

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())

import faiss
print(faiss.__version__)
```

## Future Enhancements

- [ ] SAM integration for segmentation
- [ ] Fine-tuning UI for CLIP
- [ ] Multi-GPU support
- [ ] Streaming processing for huge datasets
- [ ] Web interface for clustering
- [ ] Game-specific model profiles

## License

MIT License - See main LICENSE file

## Contributing

Contributions welcome! Please test thoroughly before submitting PRs.
