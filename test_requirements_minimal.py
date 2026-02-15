#!/usr/bin/env python3
"""
Test that requirements-minimal.txt contains all necessary dependencies
for the main application to run.
"""

import sys
import subprocess
from pathlib import Path

def test_requirements_parsing():
    """Test that requirements-minimal.txt can be parsed."""
    req_file = Path(__file__).parent / 'requirements-minimal.txt'
    
    if not req_file.exists():
        print("❌ requirements-minimal.txt not found")
        return False
    
    with open(req_file) as f:
        lines = f.readlines()
    
    # Check for essential Qt dependencies
    essential_deps = ['PyQt6>=6.6.0', 'PyOpenGL>=3.1.7', 'numpy>=1.24.0']
    found_deps = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        for dep in essential_deps:
            if dep in line:
                found_deps.append(dep)
    
    print(f"✓ Found {len(found_deps)}/{len(essential_deps)} essential dependencies")
    
    if len(found_deps) != len(essential_deps):
        print("❌ Missing essential dependencies:")
        for dep in essential_deps:
            if dep not in found_deps:
                print(f"   - {dep}")
        return False
    
    # Check that customtkinter is NOT present
    for line in lines:
        if 'customtkinter' in line.lower() and not line.strip().startswith('#'):
            print("❌ Found obsolete customtkinter dependency")
            return False
    
    print("✓ No obsolete dependencies found")
    return True

def test_import_chain():
    """Test the import chain that was causing the line 34 error."""
    print("\nTesting import chain...")
    
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        
        # Test config import (line 34 in main.py)
        from config import config, APP_NAME, APP_VERSION
        print(f"✓ Config import successful: {APP_NAME} {APP_VERSION}")
        
        # Test classifier import (line 37 in main.py)
        from classifier import TextureClassifier, ALL_CATEGORIES
        print(f"✓ Classifier import successful: {len(ALL_CATEGORIES)} categories")
        
        return True
        
    except ModuleNotFoundError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Testing requirements-minimal.txt")
    print("="*60)
    
    test1 = test_requirements_parsing()
    test2 = test_import_chain()
    
    print("\n" + "="*60)
    if test1 and test2:
        print("✓ All tests passed!")
        print("="*60)
        return 0
    else:
        print("❌ Some tests failed")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
