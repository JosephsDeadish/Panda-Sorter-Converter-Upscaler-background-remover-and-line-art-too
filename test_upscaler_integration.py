#!/usr/bin/env python3
"""
Test script to verify upscaler integration and Real-ESRGAN availability check.
This validates the changes made for upscaling support with graceful fallback.
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_upscaler_imports():
    """Test that upscaler can be imported and availability flags work."""
    print("=" * 70)
    print("Testing Upscaler Imports and Availability Flags")
    print("=" * 70)
    
    try:
        from preprocessing.upscaler import TextureUpscaler, REALESRGAN_AVAILABLE
        print("✅ Successfully imported TextureUpscaler")
        print(f"   REALESRGAN_AVAILABLE = {REALESRGAN_AVAILABLE}")
        
        # Check native lanczos
        try:
            from native_ops import NATIVE_AVAILABLE
            print(f"   NATIVE_AVAILABLE = {NATIVE_AVAILABLE}")
        except ImportError:
            print("   NATIVE_AVAILABLE = False (native module not installed)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import upscaler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_availability_includes_upscaler():
    """Test that check_feature_availability includes upscaler features."""
    print("\n" + "=" * 70)
    print("Testing Feature Availability Check")
    print("=" * 70)
    
    try:
        # Mock minimal imports to avoid Qt
        namespace = {}
        
        # Read the check_feature_availability function from main.py
        main_file = Path(__file__).parent / 'main.py'
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Find the function definition
        start_marker = "def check_feature_availability():"
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ Could not find check_feature_availability function")
            return False
        
        # Find the next function definition (end of this function)
        next_def = content.find("\ndef ", start_idx + 1)
        if next_def == -1:
            next_def = len(content)
        
        func_code = content[start_idx:next_def]
        
        # Execute the function
        exec(func_code, namespace)
        check_feature_availability = namespace['check_feature_availability']
        
        # Run the check
        features = check_feature_availability()
        
        print("\nUpscaler Feature Status:")
        print("-" * 70)
        
        # Check for upscaler keys
        if 'realesrgan' in features:
            status = "✅" if features['realesrgan'] else "⚠️ "
            print(f"{status} Real-ESRGAN: {features['realesrgan']}")
        else:
            print("❌ Real-ESRGAN key missing from features dict")
            return False
        
        if 'native_lanczos' in features:
            status = "✅" if features['native_lanczos'] else "⚠️ "
            print(f"{status} Native Lanczos: {features['native_lanczos']}")
        else:
            print("❌ Native Lanczos key missing from features dict")
            return False
        
        print("-" * 70)
        print("✅ Feature availability includes upscaler features")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upscaler_ui_availability_check():
    """Test that UI panel can check upscaler availability."""
    print("\n" + "=" * 70)
    print("Testing Upscaler UI Availability Check")
    print("=" * 70)
    
    try:
        # Try to import the upscaler panel (may fail if Qt not available)
        try:
            from ui.upscaler_panel_qt import ImageUpscalerPanelQt
            print("✅ Successfully imported ImageUpscalerPanelQt")
        except ImportError as e:
            print(f"⚠️  Could not import UI panel (Qt may not be available): {e}")
            print("   This is OK for testing - UI import is optional")
            return True
        
        # Check that the _update_method_description method exists
        if hasattr(ImageUpscalerPanelQt, '_update_method_description'):
            print("✅ _update_method_description method exists")
        else:
            print("❌ _update_method_description method missing")
            return False
        
        print("✅ UI panel has availability check capability")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pyinstaller_hooks_exist():
    """Test that PyInstaller hooks exist for basicsr and realesrgan."""
    print("\n" + "=" * 70)
    print("Testing PyInstaller Hooks")
    print("=" * 70)
    
    hooks_dir = Path(__file__).parent / '.github' / 'hooks'
    
    basicsr_hook = hooks_dir / 'hook-basicsr.py'
    realesrgan_hook = hooks_dir / 'hook-realesrgan.py'
    
    if basicsr_hook.exists():
        print(f"✅ basicsr hook exists: {basicsr_hook}")
    else:
        print(f"❌ basicsr hook missing: {basicsr_hook}")
        return False
    
    if realesrgan_hook.exists():
        print(f"✅ realesrgan hook exists: {realesrgan_hook}")
    else:
        print(f"❌ realesrgan hook missing: {realesrgan_hook}")
        return False
    
    print("✅ All PyInstaller hooks exist")
    return True


def test_build_spec_includes_upscaler():
    """Test that build spec includes upscaler in hiddenimports."""
    print("\n" + "=" * 70)
    print("Testing Build Spec Configuration")
    print("=" * 70)
    
    spec_file = Path(__file__).parent / 'build_spec_onefolder.spec'
    
    if not spec_file.exists():
        print(f"❌ Build spec not found: {spec_file}")
        return False
    
    with open(spec_file, 'r') as f:
        content = f.read()
    
    required_imports = [
        "'basicsr'",
        "'basicsr.archs'",
        "'basicsr.archs.rrdbnet_arch'",
        "'realesrgan'",
        "'realesrgan.archs'",
    ]
    
    missing = []
    for imp in required_imports:
        if imp in content:
            print(f"✅ Found {imp} in hiddenimports")
        else:
            print(f"❌ Missing {imp} in hiddenimports")
            missing.append(imp)
    
    if missing:
        print(f"❌ Missing imports: {missing}")
        return False
    
    print("✅ Build spec includes all upscaler imports")
    return True


def main():
    """Run all tests."""
    print("Testing Upscaling Support Integration")
    print("=" * 70)
    print()
    
    tests = [
        ("PyInstaller Hooks", test_pyinstaller_hooks_exist),
        ("Build Spec", test_build_spec_includes_upscaler),
        ("Upscaler Imports", test_upscaler_imports),
        ("Feature Availability", test_feature_availability_includes_upscaler),
        ("UI Availability Check", test_upscaler_ui_availability_check),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 70)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
