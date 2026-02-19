"""
Dependency Checker - Verify critical dependencies on startup
Provides clear error messages and installation instructions
"""

import sys
import logging

logger = logging.getLogger(__name__)


def check_critical_dependencies():
    """
    Check all critical dependencies and provide helpful error messages.
    
    Returns:
        tuple: (all_present: bool, missing: list, warnings: list)
    """
    missing = []
    warnings = []
    
    # CRITICAL dependencies (app won't work without these)
    critical_deps = {
        'PyQt6': 'pip install PyQt6',
        'PIL': 'pip install pillow',
        'numpy': 'pip install numpy',
        'cv2': 'pip install opencv-python',
    }
    
    # IMPORTANT dependencies (major features won't work)
    important_deps = {
        'send2trash': 'pip install send2trash',
    }
    
    # OPTIONAL dependencies (nice to have)
    optional_deps = {
        'torch': 'pip install torch',
        'transformers': 'pip install transformers',
        'onnxruntime': 'pip install onnxruntime',
        'cairosvg': 'pip install cairosvg',
    }
    
    # Check critical
    for module_name, install_cmd in critical_deps.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append((module_name, install_cmd, 'CRITICAL'))
    
    # Check important
    for module_name, install_cmd in important_deps.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append((module_name, install_cmd, 'IMPORTANT'))
    
    # Check optional (just warnings)
    for module_name, install_cmd in optional_deps.items():
        try:
            __import__(module_name)
        except ImportError:
            warnings.append((module_name, install_cmd))
    
    return (len(missing) == 0, missing, warnings)


def print_dependency_report(missing, warnings):
    """Print a comprehensive dependency report."""
    if missing:
        print("=" * 70)
        print("ERROR: MISSING DEPENDENCIES")
        print("=" * 70)
        print()
        
        critical = [m for m in missing if m[2] == 'CRITICAL']
        important = [m for m in missing if m[2] == 'IMPORTANT']
        
        if critical:
            print("CRITICAL (app will not work):")
            for module_name, install_cmd, _ in critical:
                print(f"  ❌ {module_name}")
                print(f"     Install: {install_cmd}")
            print()
        
        if important:
            print("IMPORTANT (major features disabled):")
            for module_name, install_cmd, _ in important:
                print(f"  ⚠️  {module_name}")
                print(f"     Install: {install_cmd}")
            print()
        
        print("To install all dependencies:")
        print("  pip install -r requirements.txt")
        print()
        print("=" * 70)
    
    if warnings and not missing:
        print("\n" + "=" * 70)
        print("OPTIONAL DEPENDENCIES (some features may be limited):")
        print("=" * 70)
        for module_name, install_cmd in warnings:
            print(f"  • {module_name}: {install_cmd}")
        print("=" * 70 + "\n")


if __name__ == '__main__':
    all_present, missing, warnings = check_critical_dependencies()
    print_dependency_report(missing, warnings)
    
    if not all_present:
        sys.exit(1)
    else:
        print("✅ All critical dependencies present!")
        sys.exit(0)
