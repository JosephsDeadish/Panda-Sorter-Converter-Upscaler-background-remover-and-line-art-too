# Extended Format Support Guide

## Overview

Game Texture Sorter now supports a wide range of image formats beyond the basic DDS and PNG, including modern formats like WEBP and vector formats like SVG.

## Supported Formats

### Raster (Bitmap) Formats

#### Standard Formats
- **PNG** (`.png`) - Portable Network Graphics
  - Lossless compression
  - Alpha transparency support
  - Best for UI elements and textures with transparency
  
- **JPEG** (`.jpg`, `.jpeg`, `.jpe`, `.jfif`) - Joint Photographic Experts Group
  - Lossy compression
  - No transparency support
  - Best for photographic textures
  - Smaller file sizes

- **BMP** (`.bmp`) - Windows Bitmap
  - Uncompressed or lightly compressed
  - Large file sizes
  - Universal compatibility

- **TGA** (`.tga`) - Truevision Graphics Adapter
  - Common in game development
  - Supports alpha channel
  - Uncompressed or RLE compressed

#### Modern Formats
- **WEBP** (`.webp`) - Google's modern format
  - Superior compression to JPEG/PNG
  - Supports both lossy and lossless
  - Alpha transparency support
  - Smaller file sizes

- **TIFF** (`.tif`, `.tiff`) - Tagged Image File Format
  - Professional/archival format
  - Multiple pages support
  - Various compression options
  - Large file support

- **GIF** (`.gif`) - Graphics Interchange Format
  - Animation support
  - Limited color palette (256 colors)
  - Transparency support
  - Best for small animated UI elements

- **PCX** (`.pcx`) - Personal Computer Exchange
  - Legacy PC format
  - RLE compression
  - Limited use today

#### Game-Specific Formats
- **DDS** (`.dds`) - DirectDraw Surface
  - Native game texture format
  - GPU-friendly compression (DXT1, DXT5)
  - Mipmaps support
  - Block compression

### Vector Formats (NEW!)

- **SVG** (`.svg`, `.svgz`) - Scalable Vector Graphics
  - Resolution-independent
  - XML-based format
  - Can be scaled to any size without quality loss
  - Requires `cairosvg` library for conversion
  - Automatically converted to raster when loaded

## Installation

### Basic Support
Most formats work out of the box with Pillow:
```bash
pip install pillow>=10.0.0
```

### SVG Support
For SVG vector graphics, install the additional dependency:
```bash
pip install cairosvg>=2.7.0
```

On Linux, you may also need system libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libcairo2-dev

# Fedora/RHEL
sudo dnf install cairo-devel
```

### WEBP Support
WEBP is usually included in Pillow, but if you have issues:
```bash
# Ubuntu/Debian
sudo apt-get install libwebp-dev

# Fedora/RHEL
sudo dnf install libwebp-devel
```

## Usage

### Loading Images

The `FileHandler.load_image()` method automatically handles all supported formats:

```python
from src.file_handler import FileHandler

handler = FileHandler()

# Load any supported format
img = handler.load_image(Path("texture.png"))
img = handler.load_image(Path("texture.jpg"))
img = handler.load_image(Path("texture.webp"))
img = handler.load_image(Path("icon.svg"))  # Auto-converts to raster

# Returns PIL Image object or None if failed
```

### Converting Formats

#### Single File Conversion

```python
from pathlib import Path
from src.file_handler import FileHandler

handler = FileHandler()

# DDS to PNG
handler.convert_dds_to_png(
    Path("texture.dds"),
    Path("texture.png")
)

# PNG to DDS
handler.convert_png_to_dds(
    Path("texture.png"),
    Path("texture.dds"),
    format='DXT5'  # DXT1, DXT5, etc.
)

# SVG to PNG (with custom size)
handler.convert_svg_to_png(
    Path("icon.svg"),
    Path("icon.png"),
    width=512,
    height=512
)
```

#### Batch Conversion

Convert multiple files at once:

```python
from pathlib import Path
from src.file_handler import FileHandler

handler = FileHandler()

# Get all image files
files = list(Path("input_dir").glob("*.*"))

# Convert all to PNG
output_dir = Path("output_dir")
output_dir.mkdir(exist_ok=True)

converted = handler.batch_convert(
    files,
    target_format='png',
    output_dir=output_dir,
    progress_callback=lambda i, total: print(f"Progress: {i}/{total}")
)

print(f"Converted {len(converted)} files")
```

### Supported Conversion Paths

| From → To | Supported | Notes |
|-----------|-----------|-------|
| DDS → PNG | ✅ | Full support |
| PNG → DDS | ✅ | Basic DDS write |
| SVG → PNG | ✅ | Requires cairosvg |
| Any → PNG | ✅ | Universal output |
| Any → JPEG | ✅ | Loses transparency |
| Any → WEBP | ✅ | Modern format |
| Any → Any | ✅ | Via generic converter |

## Format Detection

The system automatically detects formats by file extension:

```python
handler = FileHandler()

# Check if format is supported
is_supported = '.webp' in handler.SUPPORTED_FORMATS  # True

# Check format type
is_raster = '.png' in handler.RASTER_FORMATS  # True
is_vector = '.svg' in handler.VECTOR_FORMATS  # True
```

## Best Practices

### Choosing a Format

**For PS2 Textures:**
- **DDS** - Native format, best compatibility with games
- **PNG** - Lossless, good for editing and viewing

**For HD/4K Textures:**
- **PNG** - Lossless quality preservation
- **WEBP** - Smaller file size with similar quality
- **DDS** - For game engine compatibility

**For UI Elements:**
- **PNG** - Best for transparency and sharp edges
- **SVG** - Best for icons that need to scale
- **WEBP** - Best for space efficiency

**For Documentation/Previews:**
- **JPEG** - Smaller files for photographic content
- **WEBP** - Better compression than JPEG

### Performance Considerations

**Fast Loading:**
- PNG, JPEG, BMP (native Pillow support)
- DDS (with basic Pillow-DDS plugin)

**Slower Loading:**
- SVG (requires conversion to raster)

**File Size:**
- Smallest: WEBP (lossy) < JPEG < WEBP (lossless) < PNG
- Largest: BMP, TGA (uncompressed)

### Quality Preservation

**Lossless Formats** (no quality loss):
- PNG
- BMP
- TGA
- WEBP (lossless mode)
- TIFF

**Lossy Formats** (some quality loss):
- JPEG (adjustable quality)
- WEBP (lossy mode)

**Special Cases:**
- **DDS**: Can be lossy (DXT) or lossless (uncompressed)
- **GIF**: Limited to 256 colors (lossy for full-color images)

## Troubleshooting

### SVG Files Not Loading

**Problem:** SVG files show as unsupported

**Solution:**
```bash
pip install cairosvg
```

If that doesn't work, install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install libcairo2-dev libffi-dev

# macOS
brew install cairo libffi

# Windows
# Download cairo binaries from GTK project
```

### WEBP Files Not Loading

**Problem:** WEBP files can't be opened

**Solution:** Update Pillow:
```bash
pip install --upgrade pillow
```

Or install system WEBP libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libwebp-dev
```

### DDS Conversion Issues

**Problem:** DDS files won't convert or look corrupted

**Solution:** DDS support in basic Pillow is limited. For advanced DDS:
```bash
pip install pillow-dds
# or
pip install nvidia-dds-converter
```

## Integration with Vision Models

All formats work seamlessly with the vision models (CLIP, ViT, DINOv2):

```python
from src.preprocessing import PreprocessingPipeline
from src.vision_models import CLIPModel

# Initialize
pipeline = PreprocessingPipeline()
clip = CLIPModel()

# Process any format
for ext in ['.png', '.jpg', '.webp', '.svg', '.dds']:
    img_path = Path(f"texture{ext}")
    
    # Preprocess
    result = pipeline.process(img_path, for_model_input=True)
    
    # Classify
    predictions = clip.classify_texture(
        result['image'],
        categories=["metal", "wood", "stone"]
    )
```

## Future Enhancements

Planned format support:
- **HDR** formats (`.hdr`, `.exr`) - High dynamic range
- **KTX** (`.ktx`, `.ktx2`) - Khronos texture format
- **Basis** (`.basis`) - Universal texture compression

## See Also

- [VISION_MODELS_GUIDE.md](VISION_MODELS_GUIDE.md) - Vision model integration
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Advanced texture analysis
- [BUILD.md](BUILD.md) - Building with all dependencies
