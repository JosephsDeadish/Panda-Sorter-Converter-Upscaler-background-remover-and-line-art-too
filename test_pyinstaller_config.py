#!/usr/bin/env python3
"""
Test that PyInstaller configuration files have correct dependencies
and no deprecated imports.
"""

import sys
import re
from pathlib import Path

def test_requirements_onnx():
    """Test that requirements.txt contains onnx dependency."""
    req_file = Path(__file__).parent / 'requirements.txt'
    
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    with open(req_file) as f:
        content = f.read()
    
    # Check for onnx>=1.14.0
    if 'onnx>=1.14.0' not in content:
        print("❌ onnx>=1.14.0 not found in requirements.txt")
        return False
    
    print("✓ onnx>=1.14.0 is present in requirements.txt")
    return True

def test_setup_py_onnx():
    """Test that setup.py contains onnx in ml extras."""
    setup_file = Path(__file__).parent / 'setup.py'
    
    if not setup_file.exists():
        print("❌ setup.py not found")
        return False
    
    with open(setup_file) as f:
        content = f.read()
    
    # Check for onnx in ml extras
    if "'onnx>=1.14.0'" not in content:
        print("❌ onnx>=1.14.0 not found in setup.py ml extras")
        return False
    
    print("✓ onnx>=1.14.0 is present in setup.py ml extras")
    return True

def test_hook_torch_no_torch_six():
    """Test that hook-torch.py does not have active torch._six imports."""
    hook_file = Path(__file__).parent / 'hook-torch.py'
    
    if not hook_file.exists():
        print("❌ hook-torch.py not found")
        return False
    
    with open(hook_file) as f:
        lines = f.readlines()
    
    # Check that torch._six is not in uncommented lines
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if "'torch._six'" in stripped:
            print(f"❌ Found active torch._six import in hook-torch.py: {stripped}")
            return False
    
    print("✓ No active torch._six imports in hook-torch.py")
    return True

def test_hook_torch_onnx_imports():
    """Test that hook-torch.py contains ONNX-related imports."""
    hook_file = Path(__file__).parent / 'hook-torch.py'
    
    if not hook_file.exists():
        print("❌ hook-torch.py not found")
        return False
    
    with open(hook_file) as f:
        content = f.read()
    
    required_imports = [
        "'torch.onnx'",
        "'torch.onnx.symbolic_helper'",
        "'torch.onnx.utils'",
        "'torch.onnx._internal'",
    ]
    
    missing = []
    for imp in required_imports:
        if imp not in content:
            missing.append(imp)
    
    if missing:
        print(f"❌ Missing ONNX imports in hook-torch.py: {', '.join(missing)}")
        return False
    
    print("✓ All required ONNX imports present in hook-torch.py")
    return True


def test_hook_torch_excludes_onnx_reference():
    """Test that hook-torch.py excludes problematic onnx.reference module."""
    hook_file = Path(__file__).parent / 'hook-torch.py'
    
    if not hook_file.exists():
        print("❌ hook-torch.py not found")
        return False
    
    with open(hook_file) as f:
        content = f.read()
    
    # Check for excludedimports
    if 'excludedimports' not in content:
        print("❌ hook-torch.py missing excludedimports section")
        return False
    
    if 'onnx.reference' not in content:
        print("❌ hook-torch.py not excluding onnx.reference")
        return False
    
    print("✓ hook-torch.py excludes onnx.reference module")
    return True

def test_hook_torch_new_sharding_spec():
    """Test that hook-torch.py uses new sharding spec path."""
    hook_file = Path(__file__).parent / 'hook-torch.py'
    
    if not hook_file.exists():
        print("❌ hook-torch.py not found")
        return False
    
    with open(hook_file) as f:
        content = f.read()
    
    # Check for new path
    if "'torch.distributed._shard.sharding_spec'" not in content:
        print("❌ New sharding spec path not found in hook-torch.py")
        return False
    
    print("✓ New sharding spec path present in hook-torch.py")
    return True

def test_build_spec_no_torch_six():
    """Test that build spec files do not have active torch._six imports."""
    spec_files = [
        'build_spec_onefolder.spec',
        'build_spec_with_svg.spec',
    ]
    
    for spec_file in spec_files:
        file_path = Path(__file__).parent / spec_file
        
        if not file_path.exists():
            print(f"❌ {spec_file} not found")
            return False
        
        with open(file_path) as f:
            lines = f.readlines()
        
        # Check that torch._six is not in uncommented lines
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if "'torch._six'" in stripped:
                print(f"❌ Found active torch._six import in {spec_file}: {stripped}")
                return False
    
    print("✓ No active torch._six imports in build spec files")
    return True

def test_build_spec_onnx_import():
    """Test that build spec files contain torch.onnx import and exclude onnx.reference."""
    spec_files = [
        'build_spec_onefolder.spec',
        'build_spec_with_svg.spec',
    ]
    
    for spec_file in spec_files:
        file_path = Path(__file__).parent / spec_file
        
        if not file_path.exists():
            print(f"❌ {spec_file} not found")
            return False
        
        with open(file_path) as f:
            content = f.read()
        
        if "'torch.onnx'" not in content:
            print(f"❌ torch.onnx import not found in {spec_file}")
            return False
        
        # Check for onnx.reference in excludes
        if "'onnx.reference'" not in content:
            print(f"❌ onnx.reference not excluded in {spec_file}")
            return False
    
    print("✓ torch.onnx imports present and onnx.reference excluded in all build spec files")
    return True

def test_build_spec_sharding_comments():
    """Test that build spec files have deprecation comments for sharding_spec."""
    spec_files = [
        'build_spec_onefolder.spec',
        'build_spec_with_svg.spec',
    ]
    
    for spec_file in spec_files:
        file_path = Path(__file__).parent / spec_file
        
        if not file_path.exists():
            print(f"❌ {spec_file} not found")
            return False
        
        with open(file_path) as f:
            content = f.read()
        
        # Check for deprecation comment
        if 'Deprecated - now uses torch.distributed._shard.sharding_spec' not in content:
            print(f"❌ Deprecation comment for _sharding_spec not found in {spec_file}")
            return False
    
    print("✓ Deprecation comments present in all build spec files")
    return True

def test_python_syntax():
    """Test that all modified files have valid Python syntax."""
    files = [
        'hook-torch.py',
        'build_spec_onefolder.spec',
        'build_spec_with_svg.spec',
        'setup.py',
    ]
    
    for file_name in files:
        file_path = Path(__file__).parent / file_name
        
        if not file_path.exists():
            print(f"❌ {file_name} not found")
            return False
        
        try:
            with open(file_path) as f:
                compile(f.read(), file_name, 'exec')
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_name}: {e}")
            return False
    
    print("✓ All files have valid Python syntax")
    return True

def main():
    """Run all tests."""
    print("="*60)
    print("Testing PyInstaller Configuration Changes")
    print("="*60)
    
    tests = [
        ("requirements.txt has onnx", test_requirements_onnx),
        ("setup.py has onnx", test_setup_py_onnx),
        ("hook-torch.py: no torch._six", test_hook_torch_no_torch_six),
        ("hook-torch.py: ONNX imports", test_hook_torch_onnx_imports),
        ("hook-torch.py: excludes onnx.reference", test_hook_torch_excludes_onnx_reference),
        ("hook-torch.py: new sharding spec", test_hook_torch_new_sharding_spec),
        ("build specs: no torch._six", test_build_spec_no_torch_six),
        ("build specs: torch.onnx and excludes", test_build_spec_onnx_import),
        ("build specs: deprecation comments", test_build_spec_sharding_comments),
        ("Python syntax validation", test_python_syntax),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        result = test_func()
        results.append(result)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✓ All {total} tests passed!")
        print("="*60)
        return 0
    else:
        print(f"❌ {total - passed}/{total} tests failed")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
