# SVG Support in PS2 Texture Sorter

## Overview

The application now supports animated and interactive SVG icons that work **completely offline** without any external dependencies or downloads.

## Features

✅ **Offline SVG Support**: All SVGs are embedded in the application
✅ **Animated Icons**: Loading spinners, progress indicators, pulsing dots
✅ **Interactive SVGs**: Hover effects and state changes (via CSS/SVG animations)
✅ **Fallback Support**: Automatic PNG fallback if SVG rendering unavailable
✅ **No External Dependencies**: Works without internet connection

## SVG Files Included

### Animation Icons
- `loading_spinner.svg` - Rotating dual-circle spinner
- `pulse_indicator.svg` - Pulsing dot for active processes
- `progress_bar.svg` - Animated progress bar

### Status Icons
- `checkmark.svg` - Success indicator with draw animation
- `error_x.svg` - Error indicator with X animation

### UI Icons
- `folder.svg` - Folder icon with gradient
- `file.svg` - File icon with gradient

## Usage in Code

### Basic SVG Loading

```python
from src.utils.svg_support import SVGLoader

# Initialize loader
loader = SVGLoader()

# Load SVG and get PIL Image
image = loader.load_svg(
    svg_path="src/resources/icons/svg/checkmark.svg",
    size=(64, 64),
    fallback_png="src/resources/icons/png/checkmark.png"  # optional
)

# Use with Qt6
if image:
    from PyQt6.QtGui import QPixmap
    from PIL.ImageQt import ImageQt
    # Convert PIL Image to QPixmap
    qimage = ImageQt(image)
    pixmap = QPixmap.fromImage(qimage)
    label.setPixmap(pixmap)
```

### Creating SVGs from Templates

```python
from src.utils.svg_support import create_loading_spinner_svg, SVGLoader

# Create SVG from template
svg_string = create_loading_spinner_svg(color="#00ff00", size=64)

# Render to image
loader = SVGLoader()
image = loader.svg_from_string(svg_string, size=(64, 64))
```

### Quick Helper Function

```python
from src.utils.svg_support import load_svg_for_qt

# One-liner for Qt6 QPixmap
pixmap = load_svg_for_qt(
    svg_path="src/resources/icons/svg/loading_spinner.svg",
    size=(32, 32)
)
```

## How It Works

1. **With cairosvg** (preferred):
   - SVG is rendered to PNG in memory
   - No temporary files created
   - Supports all SVG features including animations (rendered as single frame)

2. **Without cairosvg** (fallback):
   - Looks for PNG fallback in same directory
   - Uses embedded PNG alternatives
   - Still fully functional, just no live SVG rendering

## Animation Support

SVG animations use native SVG `<animate>` and `<animateTransform>` elements:

```xml
<circle cx="50" cy="50" r="15" fill="#00ff00">
    <animate attributeName="r" values="15;20;15" dur="1s" repeatCount="indefinite"/>
</circle>
```

**Note**: When rendered via cairosvg, animations are captured as a single frame. For true animation in UI:
- Use multiple SVG frames rendered in sequence (frame-by-frame animation)
- Use Qt6 animations (QPropertyAnimation, QTimer)
- Use OpenGL rendering for smooth 60 FPS animations

## Creating New SVG Icons

### Guidelines

1. **Keep it Simple**: Simple paths render faster
2. **Use ViewBox**: `viewBox="0 0 100 100"` for scalability
3. **Inline Styles**: Avoid external stylesheets
4. **Animation**: Use SVG `<animate>` elements
5. **Colors**: Use hex colors or named colors
6. **Size**: Design at 64x64 or 100x100, scales automatically

### Example Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <!-- Your icon here -->
    <circle cx="50" cy="50" r="40" fill="#00ff00"/>
</svg>
```

## Performance

- **Memory**: Minimal - SVGs rendered on-demand
- **Speed**: Fast - cairosvg is highly optimized
- **Offline**: 100% - No network requests ever
- **Fallback**: Automatic - Uses PNG if needed

## Dependencies

### Required
- Pillow (PIL) - Already in requirements

### Optional
- cairosvg>=2.7.0 - For SVG rendering (already in requirements.txt)
- cairocffi>=1.6.0 - Cairo bindings (already in requirements.txt)

If cairosvg is not available, the system automatically falls back to PNG alternatives.

## Testing

Test SVG support:
```bash
python -m src.utils.svg_support
```

Output will show:
- cairosvg availability
- PIL availability  
- SVG rendering capability
- List of available SVG templates

## Integration Examples

### Loading Indicator

```python
from src.utils.svg_support import create_loading_spinner_svg, SVGLoader
from PyQt6.QtGui import QPixmap

loader = SVGLoader()
svg_str = create_loading_spinner_svg(color="#00ff00", size=48)
spinner_img = loader.svg_from_string(svg_str, size=(48, 48))

# Show in UI with Qt6
if spinner_img:
    from PIL.ImageQt import ImageQt
    qimage = ImageQt(spinner_img)
    pixmap = QPixmap.fromImage(qimage)
    loading_label.setPixmap(pixmap)
```

### Status Icons

```python
# Show success
success_img = loader.load_svg("icons/svg/checkmark.svg", size=(32, 32))

# Show error
error_img = loader.load_svg("icons/svg/error_x.svg", size=(32, 32))
```

## Future Enhancements

Possible improvements:
- Frame-by-frame SVG animation rendering
- SVG filter effects
- Dynamic color theming (replace colors in SVG on-the-fly)
- More icon templates
- SVG optimization tool

## Troubleshooting

**Q: SVGs not rendering?**
A: Check if cairosvg is installed. If not, the system will use PNG fallbacks.

**Q: Animations not working?**
A: SVG animations in static renders show first frame. For animation, render multiple frames or use UI animation libraries.

**Q: Performance issues?**
A: Cache rendered images. Don't re-render the same SVG repeatedly.

**Q: Want to add custom SVGs?**
A: Place them in `src/resources/icons/svg/` and use SVGLoader to load them.

## License

SVG icons created specifically for this application. Free to use within the project.
