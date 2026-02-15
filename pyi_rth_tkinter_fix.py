"""
PyInstaller Runtime Hook to Fix TCL/Tk Library Path Issues

This runtime hook ensures that tkinter can find the TCL and TK libraries
when running from a PyInstaller bundle. It fixes the error:
"failed to execute script pyi_rth_tkinter due to unhandled exception: 
tcl data directory not found"

This hook runs before the main application starts and sets up the proper
environment variables for TCL/Tk to work correctly.

It also validates that the application was fully extracted and provides
helpful error messages if files are missing.
"""

import os
import sys
from pathlib import Path


def validate_extraction():
    """
    Validate that the application was fully extracted and all required
    directories exist. This catches user errors where extraction was
    incomplete or interrupted.
    
    Returns: (bool, str) - (is_valid, error_message)
    """
    if not getattr(sys, 'frozen', False):
        return True, ""
    
    # Get the base directory
    if hasattr(sys, '_MEIPASS'):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(sys.executable).parent
    
    # Critical directories that must exist
    critical_dirs = []
    
    # For one-folder builds, check for _internal directory
    internal_dir = base_dir / '_internal'
    if internal_dir.exists():
        critical_dirs.append(internal_dir)
    
    # Check if base directory exists and is readable
    if not base_dir.exists():
        return False, f"Application directory not found: {base_dir}"
    
    # Check if we can list directory contents (indicates incomplete extraction)
    try:
        contents = list(base_dir.iterdir())
        if len(contents) == 0:
            return False, "Application directory is empty. Please re-extract the application completely."
    except (OSError, PermissionError) as e:
        return False, f"Cannot access application directory: {e}\nPlease re-extract the application."
    
    return True, ""


def fix_tkinter_paths():
    """
    Set up TCL_LIBRARY and TK_LIBRARY environment variables for PyInstaller bundles.
    
    This function locates the tcl and tk directories within the PyInstaller bundle
    and sets the appropriate environment variables so that tkinter can find them.
    
    Returns: (bool, str) - (success, error_message)
    """
    # Only run this fix when frozen (running from PyInstaller bundle)
    if not getattr(sys, 'frozen', False):
        return True, ""
    
    # First, validate that extraction is complete
    is_valid, error_msg = validate_extraction()
    if not is_valid:
        return False, error_msg
    
    # Get the base directory where PyInstaller extracts files
    # For one-folder builds: this is the directory containing the .exe
    # For one-file builds: this is sys._MEIPASS (temporary extraction directory)
    if hasattr(sys, '_MEIPASS'):
        # One-file build: files are extracted to a temporary directory
        base_dir = Path(sys._MEIPASS)
    else:
        # One-folder build: files are in the same directory as the executable
        base_dir = Path(sys.executable).parent
    
    # Try to find tcl and tk directories in common locations
    tcl_paths = [
        base_dir / 'tcl',
        base_dir / '_internal' / 'tcl',
        base_dir / 'tcl86',
        base_dir / '_internal' / 'tcl86',
        base_dir / 'tcl8.6',
        base_dir / '_internal' / 'tcl8.6',
    ]
    
    tk_paths = [
        base_dir / 'tk',
        base_dir / '_internal' / 'tk',
        base_dir / 'tk86',
        base_dir / '_internal' / 'tk86',
        base_dir / 'tk8.6',
        base_dir / '_internal' / 'tk8.6',
    ]
    
    # Find the first existing TCL directory
    tcl_dir = None
    for path in tcl_paths:
        if path.exists() and path.is_dir():
            tcl_dir = path
            break
    
    # Find the first existing TK directory
    tk_dir = None
    for path in tk_paths:
        if path.exists() and path.is_dir():
            tk_dir = path
            break
    
    # Set environment variables if directories were found
    if tcl_dir:
        os.environ['TCL_LIBRARY'] = str(tcl_dir)
        # Only print in debug mode to reduce startup overhead
        if os.environ.get('PYINSTALLER_DEBUG'):
            print(f"[Tkinter Fix] Set TCL_LIBRARY to: {tcl_dir}")
    else:
        error_msg = (
            f"TCL directory not found in: {base_dir}\n"
            f"This may indicate an incomplete extraction.\n"
            f"Please ensure you extracted ALL files from the archive.\n"
            f"Searched locations: {', '.join(str(p) for p in tcl_paths[:3])}"
        )
        return False, error_msg
    
    if tk_dir:
        os.environ['TK_LIBRARY'] = str(tk_dir)
        if os.environ.get('PYINSTALLER_DEBUG'):
            print(f"[Tkinter Fix] Set TK_LIBRARY to: {tk_dir}")
    else:
        error_msg = (
            f"TK directory not found in: {base_dir}\n"
            f"This may indicate an incomplete extraction.\n"
            f"Please ensure you extracted ALL files from the archive.\n"
            f"Searched locations: {', '.join(str(p) for p in tk_paths[:3])}"
        )
        return False, error_msg
    
    # Additional fix: Ensure _tkinter can find the tcl/tk DLLs on Windows
    if sys.platform == 'win32':
        # Add the base directory and _internal to PATH so DLLs can be found
        internal_dir = base_dir / '_internal'
        if internal_dir.exists():
            os.environ['PATH'] = str(internal_dir) + os.pathsep + os.environ.get('PATH', '')
        os.environ['PATH'] = str(base_dir) + os.pathsep + os.environ.get('PATH', '')
    
    return True, ""


def show_error_dialog(title, message):
    """
    Show a user-friendly error dialog when tkinter cannot be initialized.
    Falls back to console output if GUI is not available.
    """
    error_text = f"{title}\n\n{message}"
    
    # Try to show a message box using ctypes (Windows native)
    if sys.platform == 'win32':
        try:
            import ctypes
            MB_OK = 0x0
            MB_ICONERROR = 0x10
            ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_ICONERROR)
            return
        except Exception:
            pass
    
    # Fallback: Print to console
    print("\n" + "="*70)
    print(f"ERROR: {title}")
    print("="*70)
    print(message)
    print("="*70 + "\n")


# Run the fix immediately when this hook is imported
try:
    success, error_message = fix_tkinter_paths()
    if not success:
        show_error_dialog(
            "Application Extraction Error",
            f"{error_message}\n\n"
            "SOLUTION:\n"
            "1. Delete the partially extracted application folder\n"
            "2. Re-extract the entire archive using Windows Explorer or 7-Zip\n"
            "3. Wait for extraction to complete 100%\n"
            "4. Make sure to extract ALL files, not just the .exe\n"
            "5. Try running from a location with full read/write permissions\n\n"
            "If the problem persists, try extracting to a different location\n"
            "(e.g., Desktop or C:\\Apps) and run as administrator."
        )
        sys.exit(1)
except Exception as e:
    show_error_dialog(
        "Application Startup Error",
        f"An unexpected error occurred during startup:\n\n{str(e)}\n\n"
        "This may indicate:\n"
        "• Incomplete extraction of the application\n"
        "• Corrupted archive file\n"
        "• Insufficient permissions\n"
        "• Antivirus interference\n\n"
        "SOLUTION:\n"
        "1. Re-download the application\n"
        "2. Extract ALL files to a new folder\n"
        "3. Temporarily disable antivirus\n"
        "4. Run as administrator if needed"
    )
    sys.exit(1)
