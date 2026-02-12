# Examples Directory

This directory contains example scripts demonstrating how to use the advanced vision models and preprocessing features.

## Examples

### 1. example_clip_classification.py
Basic CLIP classification example. Shows how to classify textures into categories using zero-shot learning.

```bash
python examples/example_clip_classification.py
```

### 2. example_similarity_search.py
Build a FAISS index and perform similarity search. Find textures similar to a query texture.

```bash
python examples/example_similarity_search.py
```

### 3. example_duplicate_detection.py
Detect exact duplicates and variants. Find color swaps and brightness variants.

```bash
python examples/example_duplicate_detection.py
```

### 4. example_preprocessing.py
Upscale and enhance textures using the preprocessing pipeline.

```bash
python examples/example_preprocessing.py
```

### 5. example_complete_workflow.py
Complete workflow combining all features: preprocessing, classification, similarity search, and duplicate detection.

```bash
python examples/example_complete_workflow.py
```

## Before Running

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update paths:** Each example has placeholder paths like `"path/to/textures"`. Update these to point to your actual texture directories.

3. **GPU support (optional):** If you have a CUDA-compatible GPU, change `device='cpu'` to `device='cuda'` in the examples for faster processing.

## Notes

- First run will download model weights (CLIP, etc.) which may take a few minutes
- CLIP model is ~400MB
- Processing time depends on number of textures and hardware
- Use CPU for small datasets, GPU for large datasets
