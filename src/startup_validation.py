"""
Startup Validation Module
Validates that the application is properly extracted and ready to run.
Provides user-friendly error messages for common issues.
"""

import sys
import os
from pathlib import Path
from typing import Tuple, List


def is_frozen() -> bool:
    """Check if running from PyInstaller bundle."""
    return getattr(sys, 'frozen', False)


def get_base_dir() -> Path:
    """Get the application base directory."""
    if is_frozen():
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        else:
            return Path(sys.executable).parent
    return Path(__file__).parent.parent


def validate_extraction() -> Tuple[bool, str, List[str]]:
    """
    Validate that the application was fully extracted.
    
    Returns:
        (is_valid, error_message, missing_items)
    """
    if not is_frozen():
        return True, "", []
    
    base_dir = get_base_dir()
    missing_items = []
    
    # Check if base directory exists
    if not base_dir.exists():
        return False, f"Application directory not found: {base_dir}", ["Base directory"]
    
    # Check if directory is readable
    try:
        contents = list(base_dir.iterdir())
        if len(contents) == 0:
            return False, "Application directory is empty", ["All files"]
    except (OSError, PermissionError) as e:
        return False, f"Cannot access application directory: {e}", ["Directory access"]
    
    # For one-folder builds, check critical directories
    critical_paths = [
        base_dir / '_internal',
        base_dir / 'resources',
    ]
    
    for path in critical_paths:
        if not path.exists():
            missing_items.append(str(path.name))
    
    # Check for Python DLLs (Windows)
    if sys.platform == 'win32':
        internal_dir = base_dir / '_internal'
        if internal_dir.exists():
            python_dll_patterns = ['python*.dll', 'python*.zip']
            found_python_files = False
            for pattern in python_dll_patterns:
                if list(internal_dir.glob(pattern)):
                    found_python_files = True
                    break
            
            if not found_python_files:
                missing_items.append("Python runtime files")
    
    if missing_items:
        error_msg = (
            f"Incomplete extraction detected. Missing items:\n"
            + '\n'.join(f'  • {item}' for item in missing_items)
            + "\n\n"
            "The application may have been partially extracted or extraction was interrupted."
        )
        return False, error_msg, missing_items
    
    return True, "", []


def validate_dependencies() -> Tuple[bool, str, List[str]]:
    """
    Validate that critical Python dependencies can be imported.
    
    Returns:
        (is_valid, error_message, missing_dependencies)
    """
    missing_deps = []
    
    # Check critical dependencies
    critical_imports = [
        ('PyQt6', 'PyQt6 (Qt6 GUI framework)'),
        ('PIL', 'Pillow (Image processing)'),
        ('OpenGL', 'PyOpenGL (3D rendering)'),
    ]
    
    for module_name, description in critical_imports:
        try:
            __import__(module_name)
        except ImportError:
            missing_deps.append(description)
    
    if missing_deps:
        error_msg = (
            f"Missing critical dependencies:\n"
            + '\n'.join(f'  • {dep}' for dep in missing_deps)
            + "\n\n"
            "This usually indicates incomplete extraction or corrupted files."
        )
        return False, error_msg, missing_deps
    
    return True, "", []


def validate_optional_dependencies() -> List[Tuple[str, str, str]]:
    """
    Check optional ML/AI dependencies and return status for each.
    
    Returns:
        List of (module_name, status, install_hint) tuples.
        status is 'installed' or 'missing'.
    """
    optional_deps = [
        ('torch', 'PyTorch (deep learning framework)', 'pip install torch torchvision'),
        ('transformers', 'Transformers (CLIP, ViT models)', 'pip install transformers'),
        ('open_clip', 'open_clip (Open-source CLIP)', 'pip install open-clip-torch'),
        ('timm', 'timm (PyTorch Image Models)', 'pip install timm'),
        ('basicsr', 'BasicSR (super-resolution framework)', 'pip install basicsr realesrgan'),
        ('realesrgan', 'Real-ESRGAN (image upscaling)', 'pip install basicsr realesrgan'),
    ]
    
    results = []
    for module_name, description, install_hint in optional_deps:
        try:
            __import__(module_name)
            results.append((description, 'installed', install_hint))
        except ImportError:
            results.append((description, 'missing', install_hint))
    
    # Check native Lanczos acceleration
    try:
        import texture_ops
        results.append(('Native Lanczos acceleration', 'installed',
                        'cd native && maturin develop --release'))
    except ImportError:
        results.append(('Native Lanczos acceleration', 'missing',
                        'cd native && maturin develop --release (optional, Python fallback available)'))
    
    return results


def show_error_message(title: str, message: str):
    """
    Show a user-friendly error message.
    Tries multiple methods to ensure the user sees the error.
    """
    # Try Windows native message box first
    if sys.platform == 'win32':
        try:
            import ctypes
            MB_OK = 0x0
            MB_ICONERROR = 0x10
            ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_ICONERROR)
            return
        except Exception:
            pass
    
    # Try PyQt6 message box
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        import sys
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
        return
    except Exception:
        pass
    
    # Fallback to console
    print("\n" + "="*70)
    print(f"ERROR: {title}")
    print("="*70)
    print(message)
    print("="*70 + "\n")


def run_startup_validation() -> bool:
    """
    Run all startup validations and show error messages if needed.
    
    Returns:
        True if all validations pass, False otherwise
    """
    # Only run validation when frozen (PyInstaller bundle)
    if not is_frozen():
        return True
    
    # Validate extraction
    is_valid, error_msg, missing_items = validate_extraction()
    if not is_valid:
        show_error_message(
            "Application Extraction Error",
            f"{error_msg}\n\n"
            "SOLUTION:\n"
            "1. Delete the current application folder\n"
            "2. Re-extract the entire archive\n"
            "3. Wait for extraction to complete 100%\n"
            "4. Extract ALL files, not just the .exe\n"
            "5. Use Windows Explorer or 7-Zip to extract\n"
            "6. Extract to a location with full read/write permissions\n\n"
            "If the problem persists:\n"
            "• Try extracting to a different location (e.g., Desktop)\n"
            "• Temporarily disable antivirus software\n"
            "• Run as administrator"
        )
        return False
    
    # Validate dependencies
    is_valid, error_msg, missing_deps = validate_dependencies()
    if not is_valid:
        show_error_message(
            "Missing Dependencies",
            f"{error_msg}\n\n"
            "SOLUTION:\n"
            "1. Re-download the application from the official source\n"
            "2. Verify the download completed successfully\n"
            "3. Re-extract ALL files from the archive\n"
            "4. Scan the archive file with antivirus\n\n"
            "The application requires a complete installation."
        )
        return False
    
    return True


def optimize_memory():
    """
    Optimize memory usage during startup.
    This reduces memory footprint and improves performance.
    """
    import gc
    
    # Force garbage collection to free any startup overhead
    gc.collect()
    
    # Set garbage collection thresholds for better performance
    # These values are optimized for applications with many small objects
    gc.set_threshold(700, 10, 10)
    
    # On Windows, try to reduce memory working set
    if sys.platform == 'win32':
        try:
            import ctypes
            # Tell Windows to trim the working set
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        except Exception:
            pass
