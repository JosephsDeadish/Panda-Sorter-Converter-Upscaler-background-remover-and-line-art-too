#!/usr/bin/env python3
"""
Test Script for SVG Build Support
Tests the build infrastructure for SVG support without actually building.

This validates:
- Spec file syntax and structure
- Helper script functionality
- Documentation completeness
"""

import sys
import os
from pathlib import Path


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_spec_file_exists():
    """Test that build_spec_with_svg.spec exists."""
    spec_path = Path('build_spec_with_svg.spec')
    assert spec_path.exists(), "build_spec_with_svg.spec not found"
    print("✓ build_spec_with_svg.spec exists")
    return True


def test_spec_file_syntax():
    """Test that spec file has valid Python syntax."""
    spec_path = Path('build_spec_with_svg.spec')
    try:
        compile(spec_path.read_text(), spec_path, 'exec')
        print("✓ build_spec_with_svg.spec has valid syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in spec file: {e}")
        return False


def test_spec_file_content():
    """Test that spec file contains required components."""
    spec_path = Path('build_spec_with_svg.spec')
    content = spec_path.read_text()
    
    required_components = {
        'Cairo DLL list': 'REQUIRED_CAIRO_DLLS',
        'Search paths': 'CAIRO_SEARCH_PATHS',
        'DLL finder function': 'def find_cairo_dlls',
        'cairosvg import': "'cairosvg'",
        'cairocffi import': "'cairocffi'",
        'Console output': 'CAIRO DLL DETECTION',
        'Graceful fallback': 'if not CAIRO_SEARCH_PATHS',
    }
    
    all_ok = True
    for name, pattern in required_components.items():
        if pattern in content:
            print(f"✓ {name} present")
        else:
            print(f"✗ {name} missing")
            all_ok = False
    
    return all_ok


def test_helper_scripts_exist():
    """Test that helper scripts exist."""
    scripts = [
        'scripts/setup_cairo_dlls.py',
        'scripts/build_with_svg.py',
    ]
    
    all_ok = True
    for script in scripts:
        if Path(script).exists():
            print(f"✓ {script} exists")
        else:
            print(f"✗ {script} not found")
            all_ok = False
    
    return all_ok


def test_helper_scripts_syntax():
    """Test that helper scripts have valid Python syntax."""
    scripts = [
        'scripts/setup_cairo_dlls.py',
        'scripts/build_with_svg.py',
    ]
    
    all_ok = True
    for script_path in scripts:
        try:
            path = Path(script_path)
            compile(path.read_text(), path, 'exec')
            print(f"✓ {script_path} has valid syntax")
        except SyntaxError as e:
            print(f"✗ Syntax error in {script_path}: {e}")
            all_ok = False
    
    return all_ok


def test_documentation_exists():
    """Test that documentation exists."""
    docs = [
        'docs/SVG_BUILD_GUIDE.md',
        'scripts/README.md',
    ]
    
    all_ok = True
    for doc in docs:
        if Path(doc).exists():
            print(f"✓ {doc} exists")
        else:
            print(f"✗ {doc} not found")
            all_ok = False
    
    return all_ok


def test_documentation_completeness():
    """Test that documentation contains required sections."""
    guide_path = Path('docs/SVG_BUILD_GUIDE.md')
    content = guide_path.read_text()
    
    required_sections = [
        'Why SVG Support is Optional',
        'Installing Cairo DLLs',
        'Windows',
        'Linux',
        'macOS',
        'Building with SVG Support',
        'Troubleshooting',
        'Verification',
    ]
    
    all_ok = True
    for section in required_sections:
        if section in content:
            print(f"✓ Section '{section}' present")
        else:
            print(f"✗ Section '{section}' missing")
            all_ok = False
    
    return all_ok


def test_readme_updated():
    """Test that README.md was updated with SVG build info."""
    readme_path = Path('README.md')
    content = readme_path.read_text()
    
    checks = {
        'SVG build section': 'Building with SVG Support',
        'Standard build command': 'pyinstaller build_spec_onefolder.spec',
        'SVG build command': 'python scripts/build_with_svg.py',
        'Link to guide': 'SVG_BUILD_GUIDE.md',
    }
    
    all_ok = True
    for name, pattern in checks.items():
        if pattern in content:
            print(f"✓ {name} present")
        else:
            print(f"✗ {name} missing")
            all_ok = False
    
    return all_ok


def test_install_updated():
    """Test that INSTALL.md was updated with SVG info."""
    install_path = Path('INSTALL.md')
    content = install_path.read_text()
    
    checks = {
        'SVG section': 'SVG Support: Executables vs Running from Source',
        'Running from source': 'Running from Source (Full SVG Support)',
        'Pre-built executables': 'Pre-built Executables (SVG Optional)',
        'Why optional': 'Why SVG Support is Optional',
    }
    
    all_ok = True
    for name, pattern in checks.items():
        if pattern in content:
            print(f"✓ {name} present")
        else:
            print(f"✗ {name} missing")
            all_ok = False
    
    return all_ok


def test_original_spec_updated():
    """Test that build_spec_onefolder.spec was updated with comment."""
    spec_path = Path('build_spec_onefolder.spec')
    content = spec_path.read_text()
    
    checks = {
        'No SVG comment': 'DOES NOT include SVG support',
        'Reference to new spec': 'build_spec_with_svg.spec',
        'Reference to guide': 'SVG_BUILD_GUIDE.md',
    }
    
    all_ok = True
    for name, pattern in checks.items():
        if pattern in content:
            print(f"✓ {name} present")
        else:
            print(f"✗ {name} missing")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests."""
    print_header("Testing SVG Build Support Infrastructure")
    
    tests = [
        ("Spec File Exists", test_spec_file_exists),
        ("Spec File Syntax", test_spec_file_syntax),
        ("Spec File Content", test_spec_file_content),
        ("Helper Scripts Exist", test_helper_scripts_exist),
        ("Helper Scripts Syntax", test_helper_scripts_syntax),
        ("Documentation Exists", test_documentation_exists),
        ("Documentation Completeness", test_documentation_completeness),
        ("README Updated", test_readme_updated),
        ("INSTALL Updated", test_install_updated),
        ("Original Spec Updated", test_original_spec_updated),
    ]
    
    results = []
    for test_name, test_func in tests:
        print_header(test_name)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! SVG build support is properly configured.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
