# Alpha Color Detection and Correction Guide

## Overview

The **Alpha Correction Tool** automatically detects and corrects alpha channel colors in textures. This is particularly useful for PS2 textures that require specific alpha values for proper rendering in games and emulators.

## Features

- 🔍 **Automatic Detection** - Analyze alpha channel distribution and patterns
- 🎮 **PS2 Presets** - Optimized presets for PlayStation 2 textures
- 🎨 **Custom Thresholds** - Define your own alpha correction rules
- 📦 **Batch Processing** - Process multiple images at once
- 💾 **Safe Operations** - Optional backup before overwriting
- 📊 **Detailed Analysis** - Comprehensive alpha channel statistics

## Quick Start

### Using the Command Line

#### Basic Usage

```bash
# Fix a single image with PS2 binary preset
python -m src.cli.alpha_fix_cli image.png --preset ps2_binary

# Fix all images in a directory
python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --preset ps2_three_level

# Analyze alpha without modification
python -m src.cli.alpha_fix_cli image.png --analyze-only
```

#### List Available Presets

```bash
python -m src.cli.alpha_fix_cli --list-presets
```

### Using Python API

```python
from src.preprocessing import AlphaCorrector, AlphaCorrectionPresets

# Initialize corrector
corrector = AlphaCorrector()

# Process single image
result = corrector.process_image(
    Path("texture.png"),
    preset='ps2_binary',
    overwrite=False
)

# Batch process
results = corrector.process_batch(
    image_paths,
    output_dir=Path("output"),
    preset='ps2_three_level'
)
```

## Available Presets

### PS2 Presets

#### `ps2_binary` - PS2 Binary Alpha
- **Best for:** PS2 textures with simple transparency
- **Description:** Converts alpha to binary (0 or 255)
- **Usage:** Textures that should be either fully transparent or fully opaque
- **Common use cases:** UI icons, simple cutouts, character outlines

#### `ps2_three_level` - PS2 Three-Level Alpha
- **Best for:** PS2 textures with semi-transparency
- **Description:** Quantizes alpha to three levels (0, 128, 255)
- **Usage:** Textures with transparent, semi-transparent, and opaque areas
- **Common use cases:** Glass, smoke effects, fading UI elements

#### `ps2_ui` - PS2 UI Elements
- **Best for:** User interface textures
- **Description:** Sharp alpha cutoff at threshold 64
- **Usage:** UI elements with clean edges
- **Common use cases:** HUD elements, menus, buttons

#### `ps2_smooth` - PS2 Smooth Gradients
- **Best for:** Textures with alpha gradients
- **Description:** Normalizes gradients while preserving smoothness
- **Usage:** Textures with fading effects
- **Common use cases:** Particle effects, soft shadows, glow effects

### Generic Presets

#### `generic_binary` - Generic Binary Alpha
- **Best for:** Any platform binary alpha
- **Description:** Simple binary alpha conversion
- **Usage:** Universal binary alpha correction

#### `clean_edges` - Clean Edges
- **Best for:** Removing edge artifacts
- **Description:** Removes semi-transparent fringing around edges
- **Usage:** Textures with unwanted semi-transparent halos
- **Common use cases:** Cutout textures with edge artifacts

## Command Line Reference

### Basic Commands

```bash
# Process single image
python -m src.cli.alpha_fix_cli input.png --preset ps2_binary

# Process directory
python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --preset ps2_ui

# Process recursively
python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --recursive --preset ps2_smooth
```

### Advanced Options

```bash
# Overwrite input files (with backup)
python -m src.cli.alpha_fix_cli input_dir/ --overwrite --preset ps2_binary

# Overwrite without backup (dangerous!)
python -m src.cli.alpha_fix_cli input_dir/ --overwrite --no-backup --preset ps2_binary

# Custom thresholds
python -m src.cli.alpha_fix_cli image.png --custom 0,50,0 51,200,128 201,255,255

# Preserve gradients (only snap extremes)
python -m src.cli.alpha_fix_cli image.png --preset ps2_smooth --preserve-gradients

# Generate report
python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --report report.json
```

### Analysis Commands

```bash
# Analyze single image
python -m src.cli.alpha_fix_cli image.png --analyze-only

# Analyze directory
python -m src.cli.alpha_fix_cli input_dir/ --analyze-only --recursive

# Verbose output
python -m src.cli.alpha_fix_cli image.png --analyze-only --verbose

# Quiet mode (errors only)
python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --quiet
```

## Python API Reference

### AlphaCorrector Class

#### Initialize

```python
from src.preprocessing import AlphaCorrector

corrector = AlphaCorrector()
```

#### Detect Alpha Colors

```python
import numpy as np
from PIL import Image

# Load image
img = Image.open("texture.png")
img_array = np.array(img)

# Detect alpha patterns
detection = corrector.detect_alpha_colors(img_array)

print(f"Unique values: {detection['unique_values']}")
print(f"Patterns: {detection['patterns']}")
print(f"Is binary: {detection['is_binary']}")
```

#### Correct Alpha

```python
# Using preset
corrected, stats = corrector.correct_alpha(
    img_array,
    preset='ps2_binary'
)

# Using custom thresholds
corrected, stats = corrector.correct_alpha(
    img_array,
    custom_thresholds=[
        (0, 64, 0),      # 0-64 -> 0
        (65, 191, 128),  # 65-191 -> 128
        (192, 255, 255)  # 192-255 -> 255
    ]
)

# Preserve gradients
corrected, stats = corrector.correct_alpha(
    img_array,
    preset='ps2_smooth',
    preserve_gradients=True
)
```

#### Process Single Image

```python
from pathlib import Path

result = corrector.process_image(
    image_path=Path("input.png"),
    output_path=Path("output.png"),
    preset='ps2_binary',
    overwrite=False,
    backup=True
)

if result['success'] and result['modified']:
    print(f"Modified {result['correction']['pixels_changed']} pixels")
```

#### Batch Processing

```python
from pathlib import Path

# Find images
image_paths = list(Path("input_dir").glob("*.png"))

# Progress callback
def show_progress(current, total):
    print(f"Processing: {current}/{total}")

# Process batch
results = corrector.process_batch(
    image_paths=image_paths,
    output_dir=Path("output_dir"),
    preset='ps2_three_level',
    preserve_structure=True,
    overwrite=False,
    backup=True,
    progress_callback=show_progress
)

# Summary
successful = sum(1 for r in results if r['success'])
modified = sum(1 for r in results if r.get('modified'))
print(f"Processed: {successful}/{len(results)}, Modified: {modified}")
```

## Custom Thresholds

### Threshold Format

Thresholds are specified as tuples: `(min_alpha, max_alpha, target_alpha)`

- `min_alpha`: Minimum alpha value in range (0-255)
- `max_alpha`: Maximum alpha value in range (0-255)
- `target_alpha`: Target alpha value or `None` to preserve gradient

### Examples

#### Binary Alpha (0 or 255)

```python
thresholds = [
    (0, 127, 0),      # 0-127 -> 0 (transparent)
    (128, 255, 255)   # 128-255 -> 255 (opaque)
]
```

#### Three-Level Alpha (0, 128, 255)

```python
thresholds = [
    (0, 42, 0),       # 0-42 -> 0
    (43, 212, 128),   # 43-212 -> 128
    (213, 255, 255)   # 213-255 -> 255
]
```

#### Preserve Mid-Range Gradient

```python
thresholds = [
    (0, 30, 0),        # Very transparent -> 0
    (31, 224, None),   # Mid-range -> preserve
    (225, 255, 255)    # Nearly opaque -> 255
]
```

#### Remove Edge Fringing

```python
thresholds = [
    (0, 32, 0),        # Low alpha -> transparent
    (33, 223, None),   # Mid-range -> preserve
    (224, 255, 255)    # High alpha -> opaque
]
```

## Detection Patterns

The tool automatically detects common alpha patterns:

- **binary** - Mostly 0 or 255 (< 5% semi-transparent)
- **three_level** - Three dominant alpha values
- **gradient** - Smooth alpha transition (> 10% semi-transparent)
- **mostly_transparent** - > 50% transparent pixels
- **mostly_opaque** - > 90% opaque pixels

## Use Cases

### PS2 Game Textures

PS2 games often require specific alpha values:

```bash
# Binary alpha for character outlines
python -m src.cli.alpha_fix_cli characters/ --output fixed/ --preset ps2_binary

# Three-level for UI elements with transparency
python -m src.cli.alpha_fix_cli ui/ --output fixed/ --preset ps2_three_level

# Smooth gradients for effects
python -m src.cli.alpha_fix_cli effects/ --output fixed/ --preset ps2_smooth
```

### Batch Fix Archive

```bash
# Extract, fix, and organize
unzip texture_dump.zip -d temp/
python -m src.cli.alpha_fix_cli temp/ --output fixed/ --recursive --preset ps2_binary
# Continue with normal texture sorting...
```

### Quality Control

```bash
# Analyze before correction
python -m src.cli.alpha_fix_cli input/ --analyze-only --recursive > analysis.txt

# Apply correction
python -m src.cli.alpha_fix_cli input/ --output fixed/ --preset ps2_three_level

# Generate report
python -m src.cli.alpha_fix_cli input/ --output fixed/ --report report.json
```

### Remove Edge Artifacts

```bash
# Clean up semi-transparent fringing
python -m src.cli.alpha_fix_cli images/ --output cleaned/ --preset clean_edges
```

## Performance

- **Single image:** < 50ms for typical texture (256x256)
- **Batch processing:** ~20-30 images per second
- **Memory usage:** Minimal, processes one image at a time
- **Large images:** 4K textures (4096x4096) process in ~200ms

## Troubleshooting

### "No alpha channel" Error

**Problem:** Image doesn't have an alpha channel

**Solution:** The tool only works on images with alpha channels (RGBA). Convert your image to RGBA first:

```python
from PIL import Image
img = Image.open("image.jpg").convert("RGBA")
img.save("image.png")
```

### No Files Modified

**Problem:** Batch processing reports 0 modified files

**Solution:** Images may already have correct alpha values. Use `--analyze-only` to check:

```bash
python -m src.cli.alpha_fix_cli input/ --analyze-only --recursive
```

### Unexpected Results

**Problem:** Corrected alpha doesn't look right

**Solution:** Try different presets or custom thresholds:

```bash
# Try different presets
python -m src.cli.alpha_fix_cli image.png --preset ps2_smooth
python -m src.cli.alpha_fix_cli image.png --preset clean_edges

# Use custom thresholds
python -m src.cli.alpha_fix_cli image.png --custom 0,100,0 101,255,255
```

## Integration with Texture Sorter

The alpha correction tool integrates with the main texture sorting workflow:

1. **Pre-sorting:** Fix alpha before sorting
2. **During sorting:** Apply alpha correction as preprocessing step
3. **Post-sorting:** Clean up sorted textures

```python
from src.preprocessing import AlphaCorrector, PreprocessingPipeline

# Initialize
corrector = AlphaCorrector()
pipeline = PreprocessingPipeline(handle_alpha=True)

# Pre-process and sort
for texture_path in texture_paths:
    # Fix alpha
    corrector.process_image(texture_path, preset='ps2_binary', overwrite=True)
    
    # Continue with normal preprocessing
    result = pipeline.process(texture_path)
    # ... sorting logic ...
```

## Examples

See `examples/example_alpha_correction.py` for complete working examples:

```bash
cd examples
python example_alpha_correction.py
```

## Support

For issues, questions, or feature requests:
- Check the examples in `examples/example_alpha_correction.py`
- Run `python -m src.cli.alpha_fix_cli --list-presets` for preset details
- See test cases in `test_alpha_correction.py`

---

**Author:** Dead On The Inside / JosephsDeadish  
**Version:** 1.0.0
