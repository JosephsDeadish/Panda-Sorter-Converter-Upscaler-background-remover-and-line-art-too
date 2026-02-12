# Archive Support Guide

## Overview

PS2 Texture Sorter now includes comprehensive support for working with archive files. You can extract textures from archives, sort them, and compress the output back into archives.

## Supported Archive Formats

- **ZIP** (.zip) - Full support for reading and writing
- **7Z** (.7z) - Full support via py7zr library
- **RAR** (.rar) - Read-only support via rarfile library
- **TAR** (.tar, .tar.gz, .tgz, .tar.bz2, .tbz2, .tar.xz, .txz) - Full support

## Features

### 1. Extract from Archive (Sorting)

Extract textures from an archive file before sorting them.

**How to use:**
1. Go to the **Sorting** tab
2. Check the "📦 Extract from archive" checkbox
3. Select an archive file as your input
4. Choose an output directory
5. Click "Start Sorting"

**What happens:**
- The archive is extracted to a temporary directory
- Textures are classified and organized
- Original archive remains unchanged
- Temporary files are cleaned up automatically

### 2. Compress Output to Archive (Sorting)

After sorting, compress all organized textures into a single ZIP archive.

**How to use:**
1. Go to the **Sorting** tab
2. Check the "📦 Compress output to archive" checkbox
3. Complete the sorting operation
4. A ZIP file will be created in the output directory's parent folder

**Output:**
- Archive name: `{output_folder_name}_sorted.zip`
- Contains all organized textures in their folder structure
- Useful for sharing or storing large collections

### 3. Extract from Archive (Conversion)

Extract textures from an archive before converting them to a different format.

**How to use:**
1. Go to the **Conversion** tab
2. Check the "📦 Extract from archive" checkbox
3. Select an archive file as input
4. Choose output directory and target format
5. Click "Start Conversion"

### 4. Compress Output to Archive (Conversion)

After converting textures, compress the results into an archive.

**How to use:**
1. Go to the **Conversion** tab
2. Check the "📦 Compress output to archive" checkbox
3. Complete the conversion operation
4. A ZIP file will be created with all converted files

**Output:**
- Archive name: `{output_folder_name}_converted.zip`

### 5. Browse Archive Contents

View and explore archive contents directly in the file browser.

**How to use:**
1. Go to the **File Browser** tab
2. Click "📂 Browse"
3. Select an archive file (ZIP, 7Z, RAR, TAR)
4. Archive contents will be displayed in the file list
5. Use search and filters to find specific files

**Features:**
- View all files inside the archive
- Filter by texture formats or show all files
- Search files by name
- See file paths within the archive
- Archive icon (📦) indicates archived files

## Use Cases

### Scenario 1: Sorting Archived PS2 Dumps

You have a `game_textures.zip` file from a PS2 texture dump:

1. Open Sorting tab
2. Enable "📦 Extract from archive"
3. Select `game_textures.zip` as input
4. Set output directory
5. Choose sorting options
6. Start sorting
7. Textures are automatically extracted, sorted, and organized

### Scenario 2: Converting and Archiving

Convert DDS textures to PNG and package them:

1. Open Conversion tab
2. Enable both archive checkboxes
3. Select `textures.zip` as input (DDS files)
4. Set output directory
5. Select DDS → PNG conversion
6. Start conversion
7. Get `output_converted.zip` with all PNG files

### Scenario 3: Distributing Sorted Collections

Share your organized texture collection:

1. Sort textures normally
2. Enable "📦 Compress output to archive"
3. Complete sorting
4. Get a single ZIP file with entire sorted collection
5. Share the ZIP file with others

### Scenario 4: Previewing Archives

Preview textures before extracting:

1. Open File Browser tab
2. Click Browse and select archive
3. View texture list and search
4. Decide if you want to extract/sort

## Technical Details

### Archive Extraction

- Archives are extracted to temporary directories in your system's temp folder
- Extraction is automatic and happens before processing
- Temporary directories are cleaned up after operation completes
- Progress is shown during extraction for large archives

### Archive Creation

- Archives are created using ZIP format with DEFLATE compression
- Compression happens after sorting/conversion completes
- Archives preserve the complete folder structure
- Creation progress is tracked for large collections

### Performance

- **Small archives** (< 100 MB): Near-instant extraction
- **Medium archives** (100-500 MB): 5-15 seconds extraction
- **Large archives** (500+ MB): May take 30+ seconds
- **Compression**: Typically 50-70% of original size for textures

### Memory Usage

- Archive extraction streams files to disk
- Does not load entire archive into memory
- Safe for large archives (multiple GB)
- Temporary space required: ~2x archive size

## Troubleshooting

### "Failed to extract archive"

**Possible causes:**
- Archive file is corrupted
- Unsupported archive format
- Insufficient disk space
- File permissions issue

**Solutions:**
1. Verify archive integrity (try opening in WinRAR/7-Zip)
2. Check available disk space
3. Run application as administrator
4. Try extracting manually first

### "Archive library not available"

**Cause:** Missing optional dependency

**Solutions:**
- For 7Z support: `pip install py7zr`
- For RAR support: `pip install rarfile`
- For TAR support: Already included in Python

### Slow Archive Operations

**Tips:**
- Use ZIP format for best performance
- Avoid nested archives
- Close other applications
- Use SSD if available

### Archive Format Not Supported

**Supported formats:**
- ✅ .zip
- ✅ .7z (requires py7zr)
- ✅ .rar (requires rarfile, read-only)
- ✅ .tar, .tar.gz, .tgz
- ✅ .tar.bz2, .tbz2
- ✅ .tar.xz, .txz

**Not supported:**
- ❌ .cab (Windows Cabinet)
- ❌ .iso (Disc Images)
- ❌ Encrypted archives
- ❌ Multi-part archives

## Best Practices

1. **For Sorting:** Use extract option only when input is archived
2. **For Distribution:** Compress output for easy sharing
3. **For Storage:** Use 7Z format for best compression (requires py7zr)
4. **For Speed:** Use ZIP format for fastest operations
5. **For Compatibility:** Stick with ZIP format for maximum compatibility

## Dependencies

Archive support requires these Python packages (automatically installed with requirements.txt):

```
py7zr>=0.20.1      # 7Z support
rarfile>=4.0       # RAR support (read-only)
```

Built-in Python modules used:
- `zipfile` - ZIP support
- `tarfile` - TAR support

## Examples

### Command-line Archive Info

Check archive contents without UI:

```python
from src.utils.archive_handler import ArchiveHandler
from pathlib import Path

handler = ArchiveHandler()
archive = Path("textures.zip")

# Check if it's an archive
if handler.is_archive(archive):
    # List contents
    files = handler.list_archive_contents(archive)
    print(f"Archive contains {len(files)} files")
    
    # Extract
    extract_dir = handler.extract_archive(archive)
    print(f"Extracted to: {extract_dir}")
```

### Programmatic Archive Creation

```python
from src.utils.archive_handler import ArchiveHandler, ArchiveFormat
from pathlib import Path

handler = ArchiveHandler()

# Create ZIP archive
source = Path("sorted_textures")
output = Path("collection.zip")
handler.create_archive(source, output, ArchiveFormat.ZIP)

# Create 7Z archive (better compression)
output_7z = Path("collection.7z")
handler.create_archive(source, output_7z, ArchiveFormat.SEVEN_ZIP)
```

## See Also

- [FORMAT_SUPPORT_GUIDE.md](FORMAT_SUPPORT_GUIDE.md) - Supported texture formats
- [GAME_IDENTIFICATION.md](GAME_IDENTIFICATION.md) - Game recognition from archives
- [README.md](README.md) - Main documentation

## Support

For issues with archive support:
1. Check this guide first
2. Review error messages in the log
3. Try with a different archive format
4. Report issues on [GitHub](https://github.com/JosephsDeadish/PS2-texture-sorter/issues)

---

**Made with 🐼 by Dead On The Inside / JosephsDeadish**
