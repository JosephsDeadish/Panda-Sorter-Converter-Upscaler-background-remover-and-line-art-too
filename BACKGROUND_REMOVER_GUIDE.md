# Background Remover Tool Documentation

## Overview
AI-powered background remover for automatic subject isolation from images with transparent PNG export.

## Features

### ✓ One-Click Subject Isolation
- Automatic AI-based subject detection
- No manual masking required
- Works with any subject type (people, objects, textures)

### ✓ Batch Processing
- Process multiple images simultaneously
- Folder selection for bulk operations
- Asynchronous processing with progress tracking
- Cancellable operations

### ✓ Transparent PNG Export
- Automatic RGBA format conversion
- Optimized PNG compression
- Preserves image quality
- Configurable output directory

### ✓ Edge Refinement Slider
- Adjustable edge smoothness (0-100%)
- Gaussian blur for soft edges
- Morphological operations for clean edges
- OpenCV integration for advanced refinement

## Technical Specifications

### AI Models Supported
1. **u2net** (Default) - General purpose, most accurate
2. **u2netp** - Lightweight, faster processing
3. **u2net_human_seg** - Optimized for human subjects
4. **silueta** - Alternative general purpose model

### Dependencies
- **Required**: `rembg` - AI background removal library
- **Optional**: `opencv-python` - Advanced edge refinement
- **Built-in**: `Pillow` (PIL) - Image processing

### Installation
```bash
# Install required dependencies with CPU backend
pip install "rembg[cpu]"

# For GPU support (NVIDIA/CUDA):
pip install "rembg[gpu]"

# Install optional dependencies for advanced features
pip install opencv-python

# The AI models are downloaded automatically on first use
```

## Usage

### Python API

#### Basic Usage
```python
from src.tools.background_remover import BackgroundRemover

# Initialize
remover = BackgroundRemover()

# Check availability
if remover.is_available():
    # Remove background from file
    result = remover.remove_background_from_file(
        input_path="input.jpg",
        output_path="output.png"
    )
    
    if result.success:
        print(f"Processed in {result.processing_time:.2f}s")
```

#### Batch Processing
```python
# Process multiple files
results = remover.batch_process(
    input_paths=["image1.jpg", "image2.jpg", "image3.jpg"],
    output_dir="output_folder",
    progress_callback=lambda curr, total, name: print(f"{curr}/{total}: {name}")
)

# Check results
for result in results:
    if result.success:
        print(f"✓ {result.input_path} -> {result.output_path}")
    else:
        print(f"✗ {result.input_path}: {result.error_message}")
```

#### Edge Refinement
```python
# Set edge refinement level (0.0 to 1.0)
remover.set_edge_refinement(0.8)  # 80% smoothing

# Higher values = smoother edges
# 0.0 = sharp edges, no refinement
# 1.0 = maximum smoothing
```

#### Model Selection
```python
# Change AI model
remover.change_model('u2net_human_seg')  # Use human-optimized model

# Get available models
models = remover.get_supported_models()
print(models)  # ['u2net', 'u2netp', 'u2net_human_seg', 'silueta']
```

### UI Integration

#### Standalone Dialog
```python
from src.ui.background_remover_panel import open_background_remover_dialog

# Open as dialog window
dialog = open_background_remover_dialog(parent=main_window)
```

#### Embedded Panel
```python
from src.ui.background_remover_panel import BackgroundRemoverPanel

# Add to existing UI
panel = BackgroundRemoverPanel(parent_frame)
panel.pack(fill="both", expand=True)
```

## UI Features

### File Selection
- **Select Images** - Choose multiple image files
- **Select Folder** - Process all images in a folder
- **Clear Selection** - Reset file list

### Output Options
- **Output Directory** - Specify where to save processed images
- **Default** - Save in same directory as input with `_nobg` suffix

### Settings
- **Edge Refinement Slider** - Adjust edge smoothness (0-100%)
- **AI Model Selection** - Choose the best model for your use case
- **Alpha Matting** - Enable for better edge quality (slower)

### Progress Tracking
- Real-time progress bar
- Current file being processed
- Success/failure count
- Total processing time

## Performance

### Processing Times (Approximate)
- **u2net**: 2-5 seconds per image
- **u2netp**: 1-3 seconds per image  
- **u2net_human_seg**: 2-4 seconds per image
- **Alpha Matting**: +50% processing time

### Memory Usage
- **Model size**: 170MB (u2net), 4MB (u2netp)
- **Per image**: ~100MB during processing
- **Batch processing**: Sequential to manage memory

## Advanced Features

### Alpha Matting
Improves edge quality by analyzing color differences between foreground and background:
```python
result = remover.remove_background_from_file(
    input_path="image.jpg",
    alpha_matting=True,
    alpha_matting_foreground_threshold=240,
    alpha_matting_background_threshold=10,
    alpha_matting_erode_size=10
)
```

### Async Batch Processing
Process images in background thread without blocking UI:
```python
def on_complete(results):
    print(f"Done! {len(results)} images processed")

thread = remover.batch_process_async(
    input_paths=file_list,
    output_dir="output",
    completion_callback=on_complete
)
```

### Edge Refinement Methods
1. **Gaussian Blur** - Smooth alpha channel edges
2. **Morphological Operations** - Close small holes, clean edges
3. **Feathering** - Soft edge falloff (1-6 pixel radius)

## Integration Examples

### Texture Sorter Integration
```python
# Process textures before sorting
from src.tools.background_remover import BackgroundRemover

remover = BackgroundRemover()

# Remove backgrounds from character textures
for texture_file in character_textures:
    result = remover.remove_background_from_file(texture_file)
    if result.success:
        # Continue with sorting
        process_texture(result.output_path)
```

### Batch Export Script
```python
import sys
from pathlib import Path
from src.tools.background_remover import BackgroundRemover

def main(input_dir, output_dir):
    remover = BackgroundRemover()
    
    # Get all images
    images = list(Path(input_dir).glob("*.png"))
    
    # Process batch
    results = remover.batch_process(
        input_paths=[str(p) for p in images],
        output_dir=output_dir,
        progress_callback=lambda c, t, n: print(f"[{c}/{t}] {n}")
    )
    
    # Summary
    success = sum(1 for r in results if r.success)
    print(f"\nProcessed {success}/{len(results)} images successfully")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

## Troubleshooting

### Issue: "rembg not available" or "No onnxruntime backend found"
**Solution**: Install rembg library with CPU or GPU backend
```bash
# For CPU (recommended)
pip install "rembg[cpu]"

# For GPU (NVIDIA/CUDA)
pip install "rembg[gpu]"
```

### Issue: Slow processing
**Solutions**:
- Use `u2netp` model (faster, slightly less accurate)
- Disable alpha matting
- Reduce edge refinement level
- Process smaller batches

### Issue: Poor edge quality
**Solutions**:
- Enable alpha matting
- Increase edge refinement slider
- Try different AI models
- Install opencv-python for advanced refinement

### Issue: Out of memory
**Solutions**:
- Process smaller batches
- Use `u2netp` model (smaller memory footprint)
- Close other applications
- Resize input images before processing

## Future Enhancements

### Planned Features
- GPU acceleration support
- Custom model training
- Color replacement (not just removal)
- Shadow preservation option
- Batch preview mode
- Undo/redo functionality
- A/B comparison view

### Model Improvements
- Fine-tuned models for PS2 textures
- Specialized models for different texture types
- Ensemble model support for better accuracy

## License
Part of PS2 Texture Sorter project.
Author: Dead On The Inside / JosephsDeadish
