#!/usr/bin/env python3
"""
Test script to verify PyInstaller hook fixes for basicsr and realesrgan.
This validates the changes made to avoid module introspection at build time.
"""

import sys
from pathlib import Path

def test_hook_basicsr():
    """Test that hook-basicsr.py has the correct structure."""
    print("=" * 70)
    print("Testing hook-basicsr.py")
    print("=" * 70)
    
    hook_file = Path(__file__).parent / '.github' / 'hooks' / 'hook-basicsr.py'
    
    if not hook_file.exists():
        print("❌ hook-basicsr.py not found")
        return False
    
    with open(hook_file) as f:
        content = f.read()
    
    # Check that collect_submodules is NOT used (causes import at build time)
    if 'collect_submodules' in content and 'collect_submodules(' in content:
        print("❌ hook-basicsr.py still uses collect_submodules() - this will cause build failures")
        return False
    
    print("✅ collect_submodules() not used")
    
    # Check that hiddenimports is a static list
    if 'hiddenimports = [' not in content:
        print("❌ hiddenimports is not a static list")
        return False
    
    print("✅ hiddenimports is a static list")
    
    # Check for key modules
    required_modules = [
        "'basicsr'",
        "'basicsr.archs'",
        "'basicsr.archs.rrdbnet_arch'",
    ]
    
    for module in required_modules:
        if module not in content:
            print(f"❌ Required module {module} not found in hiddenimports")
            return False
    
    print(f"✅ All required modules present")
    
    # Check for try/except around collect_data_files
    if 'try:' not in content or 'collect_data_files' not in content or 'except Exception' not in content:
        print("❌ Missing try/except around collect_data_files")
        return False
    
    print("✅ Has error handling for data collection")
    
    # Check for informative print statements
    if 'print(f"[basicsr hook]' not in content:
        print("❌ Missing informative print statements")
        return False
    
    print("✅ Has informative print statements")
    
    return True

def test_hook_realesrgan():
    """Test that hook-realesrgan.py has the correct structure."""
    print("\n" + "=" * 70)
    print("Testing hook-realesrgan.py")
    print("=" * 70)
    
    hook_file = Path(__file__).parent / '.github' / 'hooks' / 'hook-realesrgan.py'
    
    if not hook_file.exists():
        print("❌ hook-realesrgan.py not found")
        return False
    
    with open(hook_file) as f:
        content = f.read()
    
    # Check that collect_submodules is NOT used
    if 'collect_submodules' in content and 'collect_submodules(' in content:
        print("❌ hook-realesrgan.py still uses collect_submodules() - this will cause build failures")
        return False
    
    print("✅ collect_submodules() not used")
    
    # Check that hiddenimports is a static list
    if 'hiddenimports = [' not in content:
        print("❌ hiddenimports is not a static list")
        return False
    
    print("✅ hiddenimports is a static list")
    
    # Check for key modules
    required_modules = [
        "'realesrgan'",
        "'realesrgan.archs'",
        "'realesrgan.archs.rrdbnet_arch'",
    ]
    
    for module in required_modules:
        if module not in content:
            print(f"❌ Required module {module} not found in hiddenimports")
            return False
    
    print(f"✅ All required modules present")
    
    # Check for try/except around collect_data_files
    if 'try:' not in content or 'collect_data_files' not in content or 'except Exception' not in content:
        print("❌ Missing try/except around collect_data_files")
        return False
    
    print("✅ Has error handling for data collection")
    
    # Check for informative print statements
    if 'print(f"[realesrgan hook]' not in content:
        print("❌ Missing informative print statements")
        return False
    
    print("✅ Has informative print statements")
    
    return True

def test_spec_file_workpath():
    """Test that build_spec_onefolder.spec has workpath configured."""
    print("\n" + "=" * 70)
    print("Testing build_spec_onefolder.spec")
    print("=" * 70)
    
    spec_file = Path(__file__).parent / 'build_spec_onefolder.spec'
    
    if not spec_file.exists():
        print("❌ build_spec_onefolder.spec not found")
        return False
    
    with open(spec_file) as f:
        content = f.read()
    
    # Check for tempfile import
    if 'import tempfile' not in content:
        print("❌ Missing 'import tempfile'")
        return False
    
    print("✅ imports tempfile")
    
    # Check for WORK_PATH definition
    if 'WORK_PATH = os.path.join(tempfile.gettempdir()' not in content:
        print("❌ WORK_PATH not properly defined")
        return False
    
    print("✅ WORK_PATH properly defined")
    
    # Check that workpath is used in Analysis
    if 'workpath=WORK_PATH' not in content:
        print("❌ workpath not used in Analysis()")
        return False
    
    print("✅ workpath configured in Analysis()")
    
    return True

def test_upscaler_error_handling():
    """Test that upscaler.py has improved error handling."""
    print("\n" + "=" * 70)
    print("Testing src/preprocessing/upscaler.py")
    print("=" * 70)
    
    upscaler_file = Path(__file__).parent / 'src' / 'preprocessing' / 'upscaler.py'
    
    if not upscaler_file.exists():
        print("❌ upscaler.py not found")
        return False
    
    with open(upscaler_file) as f:
        content = f.read()
    
    # Check for step-by-step imports
    if 'import basicsr' not in content:
        print("❌ Missing 'import basicsr' step")
        return False
    
    print("✅ Has separate basicsr import")
    
    if 'import realesrgan' not in content:
        print("❌ Missing 'import realesrgan' step")
        return False
    
    print("✅ Has separate realesrgan import")
    
    # Check for multiple except blocks
    if content.count('except ImportError') < 1:
        print("❌ Missing ImportError exception handling")
        return False
    
    print("✅ Has ImportError exception handling")
    
    # Check for exception type logging
    if 'type(e).__name__' not in content:
        print("❌ Missing exception type logging")
        return False
    
    print("✅ Has exception type logging")
    
    return True

def test_build_script_validation():
    """Test that build.ps1 has pre-build validation."""
    print("\n" + "=" * 70)
    print("Testing build.ps1")
    print("=" * 70)
    
    build_file = Path(__file__).parent / 'build.ps1'
    
    if not build_file.exists():
        print("❌ build.ps1 not found")
        return False
    
    with open(build_file) as f:
        content = f.read()
    
    # Check for pre-build validation section
    if '# Pre-build validation' not in content:
        print("❌ Missing pre-build validation section")
        return False
    
    print("✅ Has pre-build validation section")
    
    # Check for basicsr check
    if 'import basicsr' not in content:
        print("❌ Missing basicsr check")
        return False
    
    print("✅ Checks for basicsr")
    
    # Check for realesrgan check
    if 'import realesrgan' not in content:
        print("❌ Missing realesrgan check")
        return False
    
    print("✅ Checks for realesrgan")
    
    # Check for informative messages
    if 'basicsr found' not in content:
        print("❌ Missing success message for basicsr")
        return False
    
    print("✅ Has informative messages")
    
    return True

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PyInstaller Hook Fixes Test Suite")
    print("=" * 70 + "\n")
    
    tests = [
        ("hook-basicsr.py", test_hook_basicsr),
        ("hook-realesrgan.py", test_hook_realesrgan),
        ("build_spec_onefolder.spec", test_spec_file_workpath),
        ("upscaler.py", test_upscaler_error_handling),
        ("build.ps1", test_build_script_validation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test {name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)
