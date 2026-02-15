#!/usr/bin/env python3
"""
Verify rembg installation for background removal tool
This script checks that rembg and onnxruntime are properly installed
"""

import sys

def check_rembg():
    """Check if rembg is installed and working"""
    print("=" * 70)
    print("rembg Installation Verification")
    print("=" * 70)
    print()
    
    # Check if rembg can be imported
    print("1. Checking rembg installation...")
    try:
        import rembg
        print("   ✅ rembg is installed")
        print(f"   Version: {rembg.__version__ if hasattr(rembg, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"   ❌ rembg is NOT installed")
        print(f"   Error: {e}")
        print()
        print("   Install with: pip install 'rembg[cpu]'")
        return False
    
    # Check if onnxruntime is installed
    print("\n2. Checking onnxruntime backend...")
    try:
        import onnxruntime as ort
        print("   ✅ onnxruntime is installed")
        print(f"   Version: {ort.__version__}")
        
        # Check available execution providers
        providers = ort.get_available_providers()
        print(f"   Available providers: {', '.join(providers)}")
        
        if 'CPUExecutionProvider' in providers:
            print("   ✅ CPU execution provider available")
        if 'CUDAExecutionProvider' in providers:
            print("   ✅ CUDA (GPU) execution provider available")
            
    except ImportError as e:
        print(f"   ❌ onnxruntime is NOT installed")
        print(f"   Error: {e}")
        print()
        print("   rembg requires onnxruntime to function!")
        print("   Install with: pip install 'rembg[cpu]'")
        return False
    except Exception as e:
        print(f"   ⚠️  onnxruntime installed but may have issues: {e}")
    
    # Try to import rembg.bg (this is where the sys.exit issue happens)
    print("\n3. Checking rembg.bg module (critical for background removal)...")
    try:
        from rembg import remove
        print("   ✅ rembg.remove function imported successfully")
    except SystemExit as e:
        print(f"   ❌ rembg called sys.exit({e.code})")
        print("   This happens when onnxruntime is not properly installed")
        print()
        print("   Install with: pip install 'rembg[cpu]'")
        return False
    except ImportError as e:
        print(f"   ❌ Cannot import rembg.remove: {e}")
        return False
    
    # Check dependencies
    print("\n4. Checking rembg dependencies...")
    deps = {
        'PIL': 'Pillow',
        'numpy': 'numpy',
        'pooch': 'pooch (for model downloads)',
        'tqdm': 'tqdm (for progress bars)',
    }
    
    all_deps_ok = True
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} is missing")
            all_deps_ok = False
    
    if not all_deps_ok:
        print("\n   Install all dependencies with: pip install 'rembg[cpu]'")
        return False
    
    # Final success message
    print("\n" + "=" * 70)
    print("✅ rembg is PROPERLY INSTALLED and ready for background removal!")
    print("=" * 70)
    print()
    print("Background removal tool should work correctly in the application.")
    print()
    
    return True


def test_basic_functionality():
    """Test basic rembg functionality"""
    print("=" * 70)
    print("Testing Basic Functionality")
    print("=" * 70)
    print()
    
    try:
        from rembg import remove
        from PIL import Image
        import numpy as np
        
        print("Creating a small test image...")
        # Create a small 10x10 white image
        test_img = Image.new('RGB', (10, 10), color='white')
        
        print("Attempting background removal (this downloads model on first run)...")
        print("Note: First run may take a few minutes to download the model...")
        
        # Try to remove background
        output = remove(test_img)
        
        print("✅ Background removal test SUCCESSFUL!")
        print(f"   Input size: {test_img.size}")
        print(f"   Output size: {output.size}")
        print(f"   Output mode: {output.mode} (should have alpha channel)")
        print()
        print("The background removal tool is fully functional!")
        return True
        
    except Exception as e:
        print(f"❌ Background removal test FAILED: {e}")
        print()
        print("The tool may work for some cases but has issues.")
        return False


def main():
    """Main verification"""
    # Check installation
    install_ok = check_rembg()
    
    if not install_ok:
        print("\n⚠️  rembg is NOT properly installed!")
        print("Background removal tool will NOT work in the application.")
        print()
        print("To fix, run:")
        print("  pip uninstall -y rembg onnxruntime")
        print("  pip install 'rembg[cpu]'")
        return 1
    
    # Ask user if they want to test functionality
    print("\nDo you want to test basic background removal? (downloads model ~100MB)")
    print("This will verify the tool works end-to-end.")
    response = input("Test now? [y/N]: ").strip().lower()
    
    if response in ['y', 'yes']:
        print()
        test_ok = test_basic_functionality()
        if not test_ok:
            return 1
    else:
        print("\nSkipping functionality test.")
        print("Background removal installation is verified, but not tested.")
    
    print("\n" + "=" * 70)
    print("Verification Complete!")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
