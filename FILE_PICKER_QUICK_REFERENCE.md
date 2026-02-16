# File Picker Widget - Quick Reference Card

## Import

```python
from src.ui.widgets import FilePickerWidget
```

## Basic Usage

```python
# Single file
picker = FilePickerWidget()
picker.files_selected.connect(on_files_selected)
layout.addWidget(picker)
```

## Configurations

### Single File (Upscaler, Image Repair)
```python
FilePickerWidget(
    file_types=('*.png', '*.jpg', '*.jpeg'),
    allow_multiple=False
)
```

### Multiple Files (Batch Tools)
```python
FilePickerWidget(
    file_types=FilePickerWidget.IMAGE_FORMATS,
    allow_multiple=True
)
```

### Folder Support (Organizer)
```python
FilePickerWidget(
    file_types=('*.png', '*.jpg'),
    allow_multiple=True,
    allow_folders=True
)
```

### All Features (Advanced Tools)
```python
FilePickerWidget(
    file_types=FilePickerWidget.ALL_FORMATS,
    allow_multiple=True,
    allow_folders=True,
    allow_archives=True
)
```

## Signals

```python
# Files selected
widget.files_selected.connect(lambda files: print(files))

# Folder selected
widget.folder_selected.connect(lambda folder: print(folder))

# Archive selected
widget.archive_selected.connect(lambda archive: print(archive))
```

## Methods

```python
# Set files programmatically
widget.set_files([Path('file1.png'), Path('file2.png')])

# Get selected files
files = widget.get_selected_files()  # Returns List[Path]
file = widget.get_selected_file()    # Returns first Path or None

# Clear selection
widget.on_clear()
```

## Constants

```python
FilePickerWidget.IMAGE_FORMATS    # All image types
FilePickerWidget.ARCHIVE_FORMATS  # All archive types
FilePickerWidget.ALL_FORMATS      # Images + archives
```

## Full Example

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from src.ui.widgets import FilePickerWidget
from pathlib import Path

class MyPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        
        self.file_picker = FilePickerWidget(
            file_types=('*.png', '*.jpg'),
            allow_multiple=True,
            allow_folders=True
        )
        self.file_picker.files_selected.connect(self._on_files)
        self.file_picker.folder_selected.connect(self._on_folder)
        self.file_picker.setToolTip("Select files or folder")
        
        layout.addWidget(self.file_picker)
        self.setLayout(layout)
    
    def _on_files(self, files):
        print(f"Selected {len(files)} files")
        for f in files:
            print(f"  - {f.name}")
    
    def _on_folder(self, folder):
        print(f"Selected folder: {folder}")
```

## Features

✅ Single/multi-file selection  
✅ Folder & archive support  
✅ Drag & drop (automatic)  
✅ Recent files (last 10)  
✅ File type filtering  
✅ Custom tooltips  
✅ Material Design colors  

## Testing

```bash
python test_file_picker_widget.py      # Run tests
python demo_file_picker.py             # Run demo
```

## Documentation

- **API Docs:** `FILE_PICKER_WIDGET_DOCS.md`
- **Visual Guide:** `FILE_PICKER_VISUAL_GUIDE.md`
- **Examples:** `USAGE_EXAMPLES_FILE_PICKER.py`
- **Summary:** `FILE_PICKER_IMPLEMENTATION_SUMMARY.md`

---

**Quick Tip:** Use `FilePickerWidget.IMAGE_FORMATS` instead of hardcoding file types for consistency.
