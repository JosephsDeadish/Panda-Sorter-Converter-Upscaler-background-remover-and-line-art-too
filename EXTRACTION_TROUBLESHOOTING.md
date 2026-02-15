# Troubleshooting Extraction Issues

## Common Error: "Application directory not found"

If you see an error about missing directories or incomplete extraction:

This **usually indicates incomplete extraction** of the application.

## Why This Happens

1. **Incomplete Extraction**: The extraction process was interrupted before all files were extracted
2. **Partial Selection**: Only some files were extracted instead of the entire archive
3. **Corrupted Archive**: The downloaded file may be corrupted
4. **Insufficient Permissions**: The extraction location doesn't have proper read/write permissions
5. **Antivirus Interference**: Security software may be blocking or quarantining files

## Solution Steps

### Step 1: Verify Complete Download
1. Check the downloaded file size matches the expected size
2. Re-download if the file appears corrupted or incomplete
3. Use a reliable download manager if the file is large

### Step 2: Extract Properly
1. **Right-click** the archive file (`.zip`, `.7z`, or `.rar`)
2. Choose **"Extract All..."** or **"Extract to folder"**
3. **Wait for 100% completion** - don't interrupt the process
4. **Extract ALL files**, not just the `.exe`
5. The application is NOT a single file - it needs the entire folder structure

### Step 3: Choose a Good Location
Extract to a location with full permissions:
- ✅ Desktop
- ✅ `C:\Apps\GameTextureSorter`
- ✅ `C:\Users\YourName\Documents\GameTextureSorter`
- ❌ Avoid: Program Files (requires admin)
- ❌ Avoid: Network drives (may be slow)
- ❌ Avoid: OneDrive/Cloud folders (syncing can interfere)

### Step 4: Check Antivirus
1. Temporarily disable real-time protection
2. Extract the files
3. Add the folder to your antivirus exclusions
4. Re-enable real-time protection

### Step 5: Verify Extraction
After extraction, your folder should contain:
```
GameTextureSorter/
├── GameTextureSorter.exe       ← Main executable
├── _internal/                  ← Python runtime and libraries
│   ├── PyQt6/                 ← Qt6 libraries (CRITICAL)
│   ├── python*.dll            ← Python DLLs
│   └── ... (many other files)
├── resources/                  ← Icons, sounds, cursors
│   ├── icons/
│   ├── sounds/
│   └── cursors/
└── app_data/                   ← Config, cache, database
    ├── cache/
    ├── logs/
    └── themes/
```

**IMPORTANT**: If the `_internal` folder is missing or incomplete, the application WILL NOT work!

### Step 6: Run the Application
1. Navigate to the extracted folder
2. Double-click `GameTextureSorter.exe`
3. If you still get errors, try running as administrator (right-click → Run as administrator)

## Advanced Troubleshooting

### Error Message Analysis

The new version of the application provides detailed error messages:

1. **"Application directory is empty"**
   - Solution: Re-extract, ensuring all files are extracted

2. **"Qt libraries not found"**
   - Solution: The `_internal/PyQt6` folder is missing - re-extract completely

3. **"Cannot access application directory"**
   - Solution: Check permissions, try running as administrator

### Still Having Issues?

1. **Try a different extraction tool**:
   - Windows Explorer (built-in)
   - [7-Zip](https://www.7-zip.org/) (recommended)
   - [WinRAR](https://www.win-rar.com/)

2. **Extract to a different location**:
   - Try Desktop first (simplest)
   - Avoid cloud-synced folders
   - Avoid network drives

3. **Check system requirements**:
   - Windows 7, 8, 10, or 11
   - 64-bit operating system
   - ~200 MB free disk space
   - Administrator rights (for first run)

4. **Check file integrity**:
   - Some archives include checksums (MD5, SHA256)
   - Verify the downloaded file matches the checksum
   - Re-download if checksums don't match

## For Developers

If you're building the application, ensure:

1. The PyInstaller spec file includes PyQt6 and OpenGL:
   ```python
   hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 
                  'PyQt6.QtOpenGLWidgets', 'OpenGL.GL']
   ```

2. Qt6 libraries are properly included:
   ```python
   # PyInstaller automatically handles Qt6 plugin collection
   ```

3. The build uses one-folder mode (not one-file) for better compatibility:
   ```python
   exclude_binaries=True  # In EXE section
   ```

## Prevention Tips

1. **Always extract the entire archive** - don't just run the .exe from inside the archive
2. **Wait for extraction to complete** - be patient with large archives
3. **Use a good extraction tool** - 7-Zip is recommended
4. **Check antivirus logs** - ensure no files are being blocked
5. **Keep the entire folder together** - don't move files individually

## Summary

99% of extraction errors are caused by **incomplete extraction**.

**Quick Fix**: Delete the folder, re-extract everything, wait for completion, and try again.

---

**Application Version**: 1.0.0  
**Author**: Dead On The Inside / JosephsDeadish
