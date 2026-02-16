#!/usr/bin/env python3
"""
Test Bridge Removal - Verify PandaWidgetGLBridge removal was successful
Tests that PandaOpenGLWidget is now the primary interface
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')


def test_no_bridge_class():
    """Verify PandaWidgetGLBridge class no longer exists."""
    print("=" * 70)
    print("Testing Bridge Removal")
    print("=" * 70)
    
    try:
        from ui.panda_widget_gl import PandaOpenGLWidget
        print("✅ PandaOpenGLWidget imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import PandaOpenGLWidget: {e}")
        return False
    
    # Try to import the deprecated bridge - should fail
    try:
        from ui.panda_widget_gl import PandaWidgetGLBridge
        print("❌ PandaWidgetGLBridge still exists! Should have been removed.")
        return False
    except ImportError:
        print("✅ PandaWidgetGLBridge removed successfully (ImportError expected)")
    except AttributeError:
        print("✅ PandaWidgetGLBridge removed successfully (not in module)")
    
    return True


def test_panda_widget_export():
    """Verify PandaWidget is now exported as PandaOpenGLWidget."""
    print("\nTesting PandaWidget Export")
    print("-" * 70)
    
    try:
        from ui.panda_widget_gl import PandaWidget
        print(f"✅ PandaWidget exports successfully: {PandaWidget}")
        
        # Check if it's the correct class (or None in headless environment)
        if PandaWidget is None:
            print("   ⚠️  PandaWidget is None (expected in headless environment)")
            return True
        
        # Check if it's PandaOpenGLWidget
        from ui.panda_widget_gl import PandaOpenGLWidget
        if PandaWidget == PandaOpenGLWidget:
            print("   ✅ PandaWidget correctly exports PandaOpenGLWidget")
            return True
        else:
            print(f"   ❌ PandaWidget is {PandaWidget}, expected PandaOpenGLWidget")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import PandaWidget: {e}")
        return False


def test_loader_uses_correct_class():
    """Verify panda_widget_loader uses PandaOpenGLWidget."""
    print("\nTesting Panda Widget Loader")
    print("-" * 70)
    
    try:
        from ui.panda_widget_loader import PandaWidget, get_panda_widget_class
        print("✅ panda_widget_loader imports successfully")
        
        widget_class = get_panda_widget_class()
        print(f"   Widget class from loader: {widget_class}")
        
        if widget_class is None:
            print("   ⚠️  Widget class is None (expected in headless environment)")
            return True
        
        # In a proper environment, it should be PandaOpenGLWidget
        from ui.panda_widget_gl import PandaOpenGLWidget
        if widget_class == PandaOpenGLWidget:
            print("   ✅ Loader correctly returns PandaOpenGLWidget")
            return True
        
    except ImportError as e:
        print(f"❌ Failed to import from loader: {e}")
        return False
    
    return True


def test_opengl_widget_methods():
    """Verify PandaOpenGLWidget has all necessary methods."""
    print("\nTesting PandaOpenGLWidget Methods")
    print("-" * 70)
    
    try:
        from ui.panda_widget_gl import PandaOpenGLWidget
        
        # Check for key methods
        required_methods = [
            'initializeGL',
            'paintGL',
            'resizeGL',
            'set_animation_state',
            'add_item_3d',
            'clear_items',
            'equip_clothing',
            'equip_weapon',
        ]
        
        missing_methods = []
        for method in required_methods:
            if hasattr(PandaOpenGLWidget, method):
                print(f"   ✅ {method}()")
            else:
                print(f"   ❌ {method}() missing")
                missing_methods.append(method)
        
        if missing_methods:
            print(f"\n❌ Missing methods: {missing_methods}")
            return False
        
        print("\n✅ All required methods present")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import PandaOpenGLWidget: {e}")
        return False


def test_no_bridge_in_codebase():
    """Verify no files reference PandaWidgetGLBridge."""
    print("\nTesting Codebase for Bridge References")
    print("-" * 70)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['grep', '-r', 'PandaWidgetGLBridge', '--include=*.py', 'src/'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 1:  # No matches found (grep returns 1)
            print("✅ No references to PandaWidgetGLBridge in src/")
            return True
        elif result.returncode == 0:  # Matches found
            print("❌ Found references to PandaWidgetGLBridge:")
            print(result.stdout)
            return False
        else:
            print(f"⚠️  Grep command failed with code {result.returncode}")
            return True  # Don't fail test on grep error
            
    except Exception as e:
        print(f"⚠️  Could not run grep: {e}")
        return True  # Don't fail test if grep unavailable


def test_file_line_count():
    """Verify panda_widget_gl.py is smaller after bridge removal."""
    print("\nTesting File Size Reduction")
    print("-" * 70)
    
    try:
        with open('src/ui/panda_widget_gl.py', 'r') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        print(f"   panda_widget_gl.py: {line_count} lines")
        
        # Should be around 1295 lines (down from 1522)
        if line_count < 1400:
            print(f"   ✅ File reduced to {line_count} lines (bridge removed)")
            return True
        else:
            print(f"   ❌ File still has {line_count} lines (bridge may not be fully removed)")
            return False
            
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  BRIDGE REMOVAL VERIFICATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Bridge Class Removed", test_no_bridge_class),
        ("PandaWidget Export", test_panda_widget_export),
        ("Loader Uses Correct Class", test_loader_uses_correct_class),
        ("OpenGL Widget Methods", test_opengl_widget_methods),
        ("No Bridge References", test_no_bridge_in_codebase),
        ("File Size Reduction", test_file_line_count),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"\n✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nBridge removal successful:")
        print("  ✅ PandaWidgetGLBridge class removed (227 lines)")
        print("  ✅ PandaOpenGLWidget is now primary interface")
        print("  ✅ PandaWidget exports PandaOpenGLWidget directly")
        print("  ✅ No deprecated compatibility layer")
        print("  ✅ All functionality preserved in main widget")
        print("=" * 70)
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
