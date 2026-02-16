#!/usr/bin/env python3
"""
Test script to verify main.py can be imported and initialized without errors.
This is a minimal test that doesn't require a display.
"""
import sys
import os

# Set up offscreen platform for Qt
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def test_imports():
    """Test that all imports in main.py work correctly."""
    print("Testing imports from main.py...")
    
    try:
        # Import main module (tests module-level imports)
        import main
        print("✅ main.py imported successfully")
        
        # Test that key classes are available
        assert hasattr(main, 'TextureSorterMainWindow'), "Missing TextureSorterMainWindow"
        assert hasattr(main, 'WorkerThread'), "Missing WorkerThread"
        assert hasattr(main, 'main'), "Missing main function"
        print("✅ All expected classes and functions are present")
        
        # Test that we can access the constants
        from main import APP_NAME, APP_VERSION
        print(f"✅ App info: {APP_NAME} v{APP_VERSION}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qt_imports():
    """Test that PyQt6 can be imported."""
    print("\nTesting PyQt6 imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("✅ PyQt6 imports successful")
        return True
    except ImportError as e:
        print(f"❌ PyQt6 import error: {e}")
        return False

def test_core_imports():
    """Test that core modules can be imported."""
    print("\nTesting core module imports...")
    
    # Add src to path
    from pathlib import Path
    import importlib
    
    src_dir = Path(__file__).parent / 'src'
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    modules_to_test = [
        ('config', ['config', 'APP_NAME', 'APP_VERSION']),
        ('classifier', ['TextureClassifier', 'ALL_CATEGORIES']),
        ('lod_detector', ['LODDetector']),
        ('file_handler', ['FileHandler']),
        ('database', ['TextureDatabase']),
        ('organizer', ['OrganizationEngine', 'ORGANIZATION_STYLES']),
    ]
    
    all_passed = True
    for module_name, attributes in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            # Verify key attributes exist
            for attr in attributes:
                if not hasattr(module, attr):
                    raise ImportError(f"Module '{module_name}' missing attribute '{attr}'")
            print(f"✅ {module_name} imported")
        except ImportError as e:
            print(f"❌ {module_name} failed: {e}")
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all import tests."""
    print("=" * 60)
    print("Testing PS2 Texture Sorter - main.py Import Test")
    print("=" * 60)
    
    results = []
    
    # Test PyQt6
    results.append(("PyQt6 imports", test_qt_imports()))
    
    # Test core imports
    results.append(("Core module imports", test_core_imports()))
    
    # Test main.py import
    results.append(("main.py import", test_imports()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! main.py can be imported successfully.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
