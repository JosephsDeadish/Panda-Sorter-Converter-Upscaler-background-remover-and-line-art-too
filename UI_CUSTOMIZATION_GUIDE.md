# UI Customization System Documentation

## Overview

The PS2 Texture Sorter now includes a comprehensive UI customization system located in `src/ui/customization_panel.py`. This system provides theming, color picking, and cursor customization capabilities.

## Features

### 1. ColorWheelWidget
- **Interactive RGB color picker** with real-time preview
- **Hex color input field** with validation
- **RGB sliders** (R, G, B from 0-255) with live updates
- **Recent colors palette** - stores last 10 used colors
- **Color presets** - 6 common colors for quick selection
- **Callback support** for color change events

### 2. CursorCustomizer
- **Cursor type selector** - dropdown with options:
  - default
  - skull
  - panda
  - sword
  - arrow
  - custom
- **Size adjustment** - small (16x16), medium (32x32), large (48x48)
- **Color tint overlay** - with integrated color picker
- **Trail effects toggle** - enable/disable cursor trail
- **Preview window** - shows current cursor configuration
- **Persistent settings** - saves to config.json

### 3. ThemeManager
Built-in theme presets with full customization:

#### Available Themes:
1. **Dark Panda (Default)** - Dark background with blue accents
2. **Light Mode** - Light background with blue accents
3. **Cyberpunk** - Black with neon green/pink
4. **Neon Dreams** - Dark blue with cyan/magenta
5. **Classic Windows** - Gray with blue (Windows 95 style)
6. **Vulgar Panda** - Red/black aggressive theme

#### Theme Features:
- **Live preview** - See theme before applying
- **Apply theme globally** - Updates entire UI
- **Save custom themes** - Create and save your own
- **Load custom themes** - Browse saved themes
- **Export to JSON** - Share themes with others
- **Import from JSON** - Load themes from files
- **Theme validation** - Ensures theme integrity
- **Persistent storage** - Themes saved to `~/.ps2_texture_sorter/themes/`

### 4. Integration with Main Application

#### In main.py:
```python
# Import (lines 40-47)
try:
    from src.ui.customization_panel import open_customization_dialog
    CUSTOMIZATION_AVAILABLE = True
except ImportError:
    CUSTOMIZATION_AVAILABLE = False
```

#### Settings Tab Addition:
- New "UI Customization" section
- "Open Customization Panel" button
- Launches full customization dialog

#### Theme Loading on Startup:
```python
def _load_initial_theme(self):
    """Load theme settings from config on startup"""
    theme = config.get('ui', 'theme', default='dark')
    appearance_mode = config.get('ui', 'appearance_mode', default='dark')
    ctk.set_appearance_mode(appearance_mode)
```

#### Configuration Storage:
Themes and settings are stored in `~/.ps2_texture_sorter/`:
```
~/.ps2_texture_sorter/
├── config.json          # Main config with theme settings
└── themes/              # Custom theme JSON files
    ├── my_theme.json
    └── custom_theme.json
```

## Usage

### Opening the Customization Panel

1. Launch PS2 Texture Sorter
2. Go to "Settings" tab
3. Scroll to "UI Customization" section
4. Click "Open Customization Panel"

### Changing Themes

1. Open Customization Panel
2. Go to "Themes" tab
3. Click on a theme name to preview
4. Click "Live Preview" to test (temporary)
5. Click "Apply Theme" to save permanently

### Creating Custom Themes

1. Select a base theme
2. Click "Save as Custom"
3. Enter a name for your theme
4. Theme is saved to `~/.ps2_texture_sorter/themes/`

### Customizing Cursors

1. Go to "Cursor" tab
2. Select cursor type from dropdown
3. Choose size (small/medium/large)
4. Pick a tint color
5. Toggle trail effect if desired
6. Click "Apply Cursor"

### Using Color Picker

1. Go to "Colors" tab
2. Use RGB sliders or hex input
3. Click preset buttons for quick colors
4. Recent colors are automatically tracked
5. Selected color can be copied from hex field

## Configuration Keys

### In config.json:

```json
{
  "ui": {
    "theme": "dark_panda",
    "appearance_mode": "dark",
    "theme_colors": {
      "primary": "#1f538d",
      "secondary": "#14375e",
      ...
    },
    "cursor": "default",
    "cursor_size": "medium",
    "cursor_tint": "#ffffff",
    "cursor_trail": false
  }
}
```

## Theme JSON Structure

Custom themes must follow this structure:

```json
{
  "name": "My Custom Theme",
  "appearance_mode": "dark",
  "colors": {
    "primary": "#1f538d",
    "secondary": "#14375e",
    "background": "#1a1a1a",
    "foreground": "#ffffff",
    "accent": "#2fa572",
    "button": "#1f538d",
    "button_hover": "#2d6ba8",
    "text": "#ffffff",
    "text_secondary": "#b0b0b0",
    "border": "#333333"
  }
}
```

## API Reference

### ColorWheelWidget
```python
ColorWheelWidget(master, initial_color="#1f538d", on_color_change=callback)
```
- `initial_color`: Starting hex color
- `on_color_change`: Called when color changes with hex value

### CursorCustomizer
```python
CursorCustomizer(master, on_cursor_change=callback)
```
- `on_cursor_change`: Called with cursor config dict

### ThemeManager
```python
ThemeManager(master, on_theme_apply=callback)
```
- `on_theme_apply`: Called with theme data dict

### CustomizationPanel
```python
CustomizationPanel(master, on_settings_change=callback)
```
- `on_settings_change`: Called with (setting_type, value)

### Helper Function
```python
open_customization_dialog(parent=None)
```
Opens standalone customization dialog window.

## Offline Functionality

All features work completely offline:
- ✅ No internet required
- ✅ All themes built-in
- ✅ Local file storage
- ✅ JSON import/export
- ✅ Self-contained

## Error Handling

The system includes comprehensive error handling:
- Invalid hex colors show error dialog
- Theme validation prevents corrupted themes
- Missing files handled gracefully
- Config errors fall back to defaults
- Import errors show warning messages

## Future Enhancements

Potential additions:
- [ ] HSV color wheel visualization
- [ ] Gradient editor
- [ ] Font customization
- [ ] Custom cursor images
- [ ] Theme preview sidebar
- [ ] Color scheme generator
- [ ] Keyboard shortcuts

## Testing

Run syntax check:
```bash
python3 -m py_compile src/ui/customization_panel.py
```

Check all files:
```bash
python3 test_imports_only.py
```

## Credits

Created for PS2 Texture Sorter v1.0.0
Author: Dead On The Inside / JosephsDeadish

## License

Part of PS2 Texture Sorter project.
