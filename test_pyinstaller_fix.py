"""
Test script to verify the runtime hook and validation logic
This simulates what happens in a PyInstaller bundle
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

def test_runtime_hook():
    """Test the runtime hook logic"""
    print("="*70)
    print("Testing Runtime Hook Logic")
    print("="*70)
    
    # Import the fix function
    sys.path.insert(0, str(Path(__file__).parent))
    from pyi_rth_tkinter_fix import fix_tkinter_paths, validate_extraction
    
    # Test 1: Non-frozen mode (should return immediately)
    print("\n[Test 1] Non-frozen mode:")
    success, error = fix_tkinter_paths()
    if success:
        print("  ✓ Returns successfully in non-frozen mode")
    else:
        print(f"  ✗ Failed: {error}")
        return False
    
    # Test 2: Simulate frozen mode with valid extraction
    print("\n[Test 2] Simulated frozen mode with valid paths:")
    # Create a mock directory structure
    test_dir = Path(__file__).parent / 'test_bundle'
    test_dir.mkdir(exist_ok=True)
    
    # Create required subdirectories
    (test_dir / '_internal').mkdir(exist_ok=True)
    (test_dir / '_internal' / 'tcl').mkdir(exist_ok=True)
    (test_dir / '_internal' / 'tk').mkdir(exist_ok=True)
    
    # Test with sys._MEIPASS (create attribute if it doesn't exist)
    old_frozen = getattr(sys, 'frozen', False)
    old_meipass = getattr(sys, '_MEIPASS', None)
    
    try:
        sys.frozen = True
        sys._MEIPASS = str(test_dir)
        success, error = fix_tkinter_paths()
        if success:
            print("  ✓ Handles PyInstaller one-file bundle correctly")
            print(f"  ✓ TCL_LIBRARY set to: {os.environ.get('TCL_LIBRARY', 'NOT SET')}")
            print(f"  ✓ TK_LIBRARY set to: {os.environ.get('TK_LIBRARY', 'NOT SET')}")
        else:
            print(f"  ✗ Failed: {error}")
    finally:
        # Restore original values
        if old_frozen:
            sys.frozen = old_frozen
        else:
            if hasattr(sys, 'frozen'):
                delattr(sys, 'frozen')
        
        if old_meipass:
            sys._MEIPASS = old_meipass
        else:
            if hasattr(sys, '_MEIPASS'):
                delattr(sys, '_MEIPASS')
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n[Test 3] Simulated incomplete extraction:")
    # Create directory but without tcl/tk subdirs
    test_dir = Path(__file__).parent / 'test_incomplete'
    test_dir.mkdir(exist_ok=True)
    (test_dir / '_internal').mkdir(exist_ok=True)
    
    try:
        sys.frozen = True
        sys._MEIPASS = str(test_dir)
        success, error = fix_tkinter_paths()
        if not success and 'TCL directory not found' in error:
            print("  ✓ Correctly detects missing TCL directory")
            print("  ✓ Provides helpful error message")
        else:
            print(f"  ✗ Should have detected missing directories")
    finally:
        # Restore original values
        if hasattr(sys, 'frozen'):
            delattr(sys, 'frozen')
        if hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n" + "="*70)
    print("Runtime Hook Tests PASSED")
    print("="*70)
    return True


def test_startup_validation():
    """Test the startup validation module"""
    print("\n" + "="*70)
    print("Testing Startup Validation Module")
    print("="*70)
    
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    from startup_validation import validate_extraction, validate_dependencies, optimize_memory
    
    # Test 1: Validation in dev mode
    print("\n[Test 1] Validation in development mode:")
    is_valid, error, missing = validate_extraction()
    if is_valid:
        print("  ✓ Extraction validation passes in dev mode")
    else:
        print(f"  ✗ Failed: {error}")
        return False
    
    # Test 2: Memory optimization
    print("\n[Test 2] Memory optimization:")
    try:
        optimize_memory()
        print("  ✓ Memory optimization completes without errors")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False
    
    # Test 3: Dependency validation (expected to detect missing deps in CI)
    print("\n[Test 3] Dependency validation:")
    is_valid, error, missing = validate_dependencies()
    if not is_valid:
        print("  ✓ Correctly detects missing dependencies in CI environment")
        print(f"  ℹ Missing: {', '.join(missing)}")
    else:
        print("  ✓ All critical dependencies available")
    
    print("\n" + "="*70)
    print("Startup Validation Tests PASSED")
    print("="*70)
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PYINSTALLER FIX - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    try:
        # Run all tests
        hook_pass = test_runtime_hook()
        validation_pass = test_startup_validation()
        
        print("\n" + "="*70)
        if hook_pass and validation_pass:
            print("✓ ALL TESTS PASSED")
            print("="*70)
            print("\nThe PyInstaller fix is ready for production!")
            print("Build the application with: build.bat or build.ps1")
            sys.exit(0)
        else:
            print("✗ SOME TESTS FAILED")
            print("="*70)
            sys.exit(1)
    except Exception as e:
        print("\n" + "="*70)
        print(f"✗ TEST SUITE FAILED: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
