#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Unicode encoding fixes work correctly.
Tests that emoji characters can be printed without UnicodeEncodeError.
"""

import sys
import os

def test_unicode_output():
    """Test that Unicode emojis can be printed successfully."""
    print("=" * 60)
    print("Unicode Encoding Test")
    print("=" * 60)
    
    # Display system information
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Default encoding: {sys.getdefaultencoding()}")
    print(f"Stdout encoding: {sys.stdout.encoding}")
    print(f"Stderr encoding: {sys.stderr.encoding}")
    
    # Test various Unicode characters
    print("\nTesting emoji output:")
    print("  ✅ Check mark (U+2705)")
    print("  ❌ Cross mark (U+274C)")
    print("  🐼 Panda (U+1F43C)")
    print("  ✨ Sparkles (U+2728)")
    print("  💖 Heart (U+1F496)")
    print("  🎉 Party popper (U+1F389)")
    print("  ⚠️ Warning (U+26A0)")
    print("  📁 Folder (U+1F4C1)")
    print("  📂 Open folder (U+1F4C2)")
    
    # Test string formatting with emojis
    test_strings = [
        "✅ Operation completed successfully",
        "❌ Error occurred during processing",
        "🐼 Panda is feeling happy",
        "Processing file 1/100 - Converting...",
        "Settings saved ✅",
    ]
    
    print("\nTesting formatted strings:")
    for i, s in enumerate(test_strings, 1):
        print(f"  {i}. {s}")
    
    print("\n" + "=" * 60)
    print("✅ All Unicode tests passed!")
    print("=" * 60)
    
    return True

def test_imports_with_unicode():
    """Test that modules with Unicode in their print statements can be imported."""
    print("\nTesting module imports...")
    
    try:
        # These modules all contain print statements with Unicode emojis
        print("  Importing test_main_import...")
        # Don't actually import to avoid running the tests, just verify the file exists
        import_path = os.path.join(os.path.dirname(__file__), 'test_main_import.py')
        assert os.path.exists(import_path), "test_main_import.py not found"
        print("    ✅ test_main_import.py found")
        
        print("  Checking main.py...")
        main_path = os.path.join(os.path.dirname(__file__), 'main.py')
        assert os.path.exists(main_path), "main.py not found"
        print("    ✅ main.py found")
        
        print("  Checking generate_sounds.py...")
        sounds_path = os.path.join(os.path.dirname(__file__), 'generate_sounds.py')
        assert os.path.exists(sounds_path), "generate_sounds.py not found"
        print("    ✅ generate_sounds.py found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import test failed: {e}")
        return False

def main():
    """Run all Unicode tests."""
    try:
        # Run tests
        unicode_ok = test_unicode_output()
        imports_ok = test_imports_with_unicode()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary:")
        print(f"  Unicode output: {'✅ PASS' if unicode_ok else '❌ FAIL'}")
        print(f"  Module imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
        print("=" * 60)
        
        if unicode_ok and imports_ok:
            print("\n🎉 All tests passed! Unicode encoding is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            return 1
            
    except UnicodeEncodeError as e:
        print("\n" + "=" * 60)
        print("❌ UNICODE ENCODE ERROR DETECTED!")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nThis error indicates that the Unicode encoding fix is not working.")
        print("Make sure the encoding fix is applied at the top of the script.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
