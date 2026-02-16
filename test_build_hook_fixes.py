#!/usr/bin/env python3
"""
Test script to verify the build hook fixes for basicsr and realesrgan.
Tests that the hooks don't use introspection and that excludedimports are properly set.
"""

import sys
from pathlib import Path


def test_basicsr_hook():
    """Verify basicsr hook doesn't use collect_submodules."""
    print("=" * 70)
    print("Testing basicsr hook")
    print("=" * 70)
    
    hook_path = Path('.github/hooks/hook-basicsr.py')
    if not hook_path.exists():
        print(f"❌ Hook file not found: {hook_path}")
        return False
    
    content = hook_path.read_text()
    
    # Check that it doesn't use collect_submodules
    if 'collect_submodules' in content:
        print("❌ Hook still uses collect_submodules (should be removed)")
        return False
    
    # Check that it has hiddenimports
    if 'hiddenimports = [' not in content:
        print("❌ Hook doesn't define hiddenimports list")
        return False
    
    # Check for expected modules
    expected_modules = [
        'basicsr',
        'basicsr.archs',
        'basicsr.archs.rrdbnet_arch',
    ]
    
    for module in expected_modules:
        if f"'{module}'" not in content:
            print(f"❌ Module '{module}' not found in hiddenimports")
            return False
    
    # Check for "no introspection" message
    if 'no introspection' not in content.lower():
        print("⚠️  Warning: Hook doesn't mention 'no introspection' in output")
    
    print("✅ basicsr hook correctly configured:")
    print("   - No collect_submodules()")
    print("   - Has hiddenimports list with required modules")
    print("   - Uses forced includes without introspection")
    return True


def test_realesrgan_hook():
    """Verify realesrgan hook doesn't use collect_submodules."""
    print("\n" + "=" * 70)
    print("Testing realesrgan hook")
    print("=" * 70)
    
    hook_path = Path('.github/hooks/hook-realesrgan.py')
    if not hook_path.exists():
        print(f"❌ Hook file not found: {hook_path}")
        return False
    
    content = hook_path.read_text()
    
    # Check that it doesn't use collect_submodules
    if 'collect_submodules' in content:
        print("❌ Hook still uses collect_submodules (should be removed)")
        return False
    
    # Check that it has hiddenimports
    if 'hiddenimports = [' not in content:
        print("❌ Hook doesn't define hiddenimports list")
        return False
    
    # Check for expected modules
    expected_modules = [
        'realesrgan',
        'realesrgan.archs',
        'realesrgan.archs.rrdbnet_arch',
    ]
    
    for module in expected_modules:
        if f"'{module}'" not in content:
            print(f"❌ Module '{module}' not found in hiddenimports")
            return False
    
    # Check for "no introspection" message
    if 'no introspection' not in content.lower():
        print("⚠️  Warning: Hook doesn't mention 'no introspection' in output")
    
    print("✅ realesrgan hook correctly configured:")
    print("   - No collect_submodules()")
    print("   - Has hiddenimports list with required modules")
    print("   - Uses forced includes without introspection")
    return True


def test_build_spec_excludedimports():
    """Verify build spec has excludedimports for onnxscript."""
    print("\n" + "=" * 70)
    print("Testing build spec excludedimports")
    print("=" * 70)
    
    spec_path = Path('build_spec_onefolder.spec')
    if not spec_path.exists():
        print(f"❌ Spec file not found: {spec_path}")
        return False
    
    content = spec_path.read_text()
    
    # Check for excludedimports parameter
    if 'excludedimports=' not in content:
        print("❌ Spec file doesn't have excludedimports parameter")
        return False
    
    # Check for onnxscript in excludedimports
    expected_excludes = [
        'onnxscript',
        'torch.onnx._internal.exporter._torchlib.ops',
    ]
    
    for exclude in expected_excludes:
        if f"'{exclude}'" not in content:
            print(f"❌ Module '{exclude}' not found in excludedimports")
            return False
    
    print("✅ Build spec excludedimports correctly configured:")
    print("   - Has excludedimports parameter")
    print("   - Excludes onnxscript")
    print("   - Excludes torch.onnx._internal.exporter._torchlib.ops")
    return True


def test_build_spec_windows_long_path():
    """Verify build spec has Windows long path support."""
    print("\n" + "=" * 70)
    print("Testing Windows long path support")
    print("=" * 70)
    
    spec_path = Path('build_spec_onefolder.spec')
    if not spec_path.exists():
        print(f"❌ Spec file not found: {spec_path}")
        return False
    
    content = spec_path.read_text()
    
    # Check for Windows long path support
    if 'WINDOWS LONG PATH SUPPORT' not in content:
        print("❌ Spec file doesn't have Windows long path support section")
        return False
    
    # Check for winreg import
    if 'import winreg' not in content:
        print("❌ Spec file doesn't import winreg for long path check")
        return False
    
    # Check for LongPathsEnabled check
    if 'LongPathsEnabled' not in content:
        print("❌ Spec file doesn't check LongPathsEnabled registry key")
        return False
    
    print("✅ Build spec Windows long path support correctly configured:")
    print("   - Has WINDOWS LONG PATH SUPPORT section")
    print("   - Checks LongPathsEnabled registry key")
    print("   - Provides helpful warning message")
    return True


def test_upscaler_error_handling():
    """Verify upscaler has comprehensive error handling."""
    print("\n" + "=" * 70)
    print("Testing upscaler error handling")
    print("=" * 70)
    
    upscaler_path = Path('src/preprocessing/upscaler.py')
    if not upscaler_path.exists():
        print(f"❌ Upscaler file not found: {upscaler_path}")
        return False
    
    content = upscaler_path.read_text()
    
    # Check for comprehensive error handling
    checks = [
        ('try:', 'Has try block for Real-ESRGAN import'),
        ('except ImportError', 'Catches ImportError'),
        ('except Exception', 'Catches general exceptions'),
        ('logger.warning', 'Logs warnings for missing packages'),
        ('REALESRGAN_AVAILABLE = False', 'Sets availability flag to False on error'),
        ('⚠️', 'Uses warning emoji in messages'),
    ]
    
    for check, description in checks:
        if check not in content:
            print(f"❌ Missing: {description} ('{check}')")
            return False
    
    print("✅ Upscaler error handling correctly configured:")
    print("   - Has try/except blocks for imports")
    print("   - Catches both ImportError and generic Exception")
    print("   - Logs helpful warning messages")
    print("   - Sets REALESRGAN_AVAILABLE flag appropriately")
    return True


def test_main_upscaler_diagnostics():
    """Verify main.py has upscaler diagnostics."""
    print("\n" + "=" * 70)
    print("Testing main.py upscaler diagnostics")
    print("=" * 70)
    
    main_path = Path('main.py')
    if not main_path.exists():
        print(f"❌ main.py not found: {main_path}")
        return False
    
    content = main_path.read_text()
    
    # Check for 'upscaler' in features dict
    if "'upscaler':" not in content:
        print("❌ 'upscaler' key not found in features dict")
        return False
    
    # Check for REALESRGAN_AVAILABLE import
    if 'from preprocessing.upscaler import REALESRGAN_AVAILABLE' not in content:
        print("❌ REALESRGAN_AVAILABLE not imported from upscaler")
        return False
    
    # Check for upscaler status in startup diagnostics
    if 'Real-ESRGAN upscaler' not in content:
        print("❌ Upscaler status not shown in startup diagnostics")
        return False
    
    print("✅ main.py upscaler diagnostics correctly configured:")
    print("   - Has 'upscaler' in features dict")
    print("   - Imports REALESRGAN_AVAILABLE")
    print("   - Shows upscaler status in startup diagnostics")
    return True


def main():
    """Run all tests."""
    print("Testing Build Hook Fixes")
    print("=" * 70)
    print()
    
    tests = [
        ("basicsr hook", test_basicsr_hook),
        ("realesrgan hook", test_realesrgan_hook),
        ("build spec excludedimports", test_build_spec_excludedimports),
        ("Windows long path support", test_build_spec_windows_long_path),
        ("upscaler error handling", test_upscaler_error_handling),
        ("main.py upscaler diagnostics", test_main_upscaler_diagnostics),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    for name, result in results:
        if result:
            print(f"✅ PASS: {name}")
            passed += 1
        else:
            print(f"❌ FAIL: {name}")
            failed += 1
    
    print("=" * 70)
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
