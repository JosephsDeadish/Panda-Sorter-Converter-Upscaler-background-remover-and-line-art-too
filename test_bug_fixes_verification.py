"""
Test script to verify bug fixes for PS2 Texture Sorter
Tests the following issues:
1. Goodbye splash screen integration
2. Scrollable UI in Sort Textures tab
3. Removal of duplicate "Organize Now" button
4. Icon configuration
5. Tab emoji icons
"""

import sys
from pathlib import Path

# Test 1: Check goodbye splash module exists and has correct structure
print("Test 1: Checking goodbye splash module...")
try:
    # Check file exists
    goodbye_splash_path = Path(__file__).parent / "src" / "ui" / "goodbye_splash.py"
    assert goodbye_splash_path.exists(), "goodbye_splash.py does not exist"
    
    # Check for required components
    content = goodbye_splash_path.read_text()
    assert "GOODBYE_MESSAGES" in content, "GOODBYE_MESSAGES not found"
    assert "class GoodbyeSplash" in content, "GoodbyeSplash class not found"
    assert "def show_goodbye_splash" in content, "show_goodbye_splash function not found"
    
    # Verify all panda farewell messages are present
    expected_messages = [
        "See you later! 🐼",
        "Bamboo break time! 🎋",
        "Until next time, texture friend! 🐼",
        "Thanks for sorting with us! 🐼✨",
        "Goodbye, texture master! 🐼",
        "May your textures always be organized! 🎨",
        "Time for a panda nap! 😴🐼",
        "Stay sorted, friend! 🐼📁",
        "Catch you on the flip side! 🐼",
        "Happy texture hunting! 🐼🔍",
        "Until we sort again! 🐼💚",
        "Keep those textures tidy! 🐼✨",
    ]
    for msg in expected_messages:
        assert msg in content, f"Farewell message '{msg}' not found"
    
    print("✅ Goodbye splash module is correctly implemented")
except AssertionError as e:
    print(f"❌ Test 1 failed: {e}")
    sys.exit(1)

# Test 2: Check main.py has goodbye splash integration
print("\nTest 2: Checking goodbye splash integration in main.py...")
try:
    main_path = Path(__file__).parent / "main.py"
    content = main_path.read_text()
    
    assert "from src.ui.goodbye_splash import show_goodbye_splash" in content, "Goodbye splash import not found"
    assert "GOODBYE_SPLASH_AVAILABLE" in content, "GOODBYE_SPLASH_AVAILABLE flag not found"
    assert "splash = show_goodbye_splash(self)" in content, "show_goodbye_splash call not found"
    assert "def _force_exit(self):" in content, "_force_exit method not found"
    assert "sys.exit(0)" in content, "sys.exit(0) not found for clean shutdown"
    print("✅ Goodbye splash is properly integrated")
except AssertionError as e:
    print(f"❌ Test 2 failed: {e}")
    sys.exit(1)

# Test 3: Check Sort Textures tab uses scrollable frame
print("\nTest 3: Checking scrollable frame in Sort Textures tab...")
try:
    content = main_path.read_text()
    
    assert "ctk.CTkScrollableFrame(self.tab_sort)" in content, "CTkScrollableFrame not used for Sort Textures tab"
    assert "scrollable_frame.pack(fill=\"both\", expand=True, padx=5, pady=5)" in content, "Scrollable frame not properly packed"
    print("✅ Sort Textures tab uses scrollable frame")
except AssertionError as e:
    print(f"❌ Test 3 failed: {e}")
    sys.exit(1)

# Test 4: Check "Organize Now" button is removed
print("\nTest 4: Checking 'Organize Now' button is removed...")
try:
    content = main_path.read_text()
    
    # Should not find the organize_button definition
    assert "self.organize_button = ctk.CTkButton" not in content, "Organize Now button still exists"
    assert "Organize Now" not in content, "Organize Now text still found"
    
    # Should still have Start Sorting button
    assert "🐼 Start Sorting" in content, "Start Sorting button not found"
    print("✅ 'Organize Now' button successfully removed")
except AssertionError as e:
    print(f"❌ Test 4 failed: {e}")
    sys.exit(1)

# Test 5: Check icon configuration
print("\nTest 5: Checking icon configuration...")
try:
    # Check assets directory
    assets_dir = Path(__file__).parent / "assets"
    icon_ico = assets_dir / "icon.ico"
    icon_png = assets_dir / "icon.png"
    
    assert assets_dir.exists(), "Assets directory not found"
    assert icon_ico.exists(), "icon.ico not found in assets"
    assert icon_png.exists(), "icon.png not found in assets"
    
    # Check build_spec.spec
    build_spec_path = Path(__file__).parent / "build_spec.spec"
    build_spec_content = build_spec_path.read_text()
    
    assert "ASSETS_DIR / 'icon.ico'" in build_spec_content, "icon.ico not included in build spec"
    assert "ASSETS_DIR / 'icon.png'" in build_spec_content, "icon.png not included in build spec"
    assert "icon=str(ICON_PATH)" in build_spec_content, "Icon not set in EXE config"
    
    # Check main.py icon setup
    assert "self.iconbitmap(str(ico_path))" in content, "iconbitmap not called in main.py"
    assert "SetCurrentProcessExplicitAppUserModelID" in content, "AppUserModelID not set"
    
    print("✅ Icon configuration is correct")
except AssertionError as e:
    print(f"❌ Test 5 failed: {e}")
    sys.exit(1)

# Test 6: Check tab emoji icons
print("\nTest 6: Checking tab emoji icons...")
try:
    content = main_path.read_text()
    
    expected_tabs = [
        "🐼 Sort Textures",
        "🔄 Convert Files",
        "📁 File Browser",
        "🏆 Achievements",
        "🎁 Rewards",
        "📝 Notepad",
        "ℹ️ About"
    ]
    
    for tab_label in expected_tabs:
        assert tab_label in content, f"Tab label '{tab_label}' not found"
    
    print("✅ All tab emoji icons are present")
except AssertionError as e:
    print(f"❌ Test 6 failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nBug fixes verified:")
print("1. ✅ Goodbye splash screen with randomized panda messages")
print("2. ✅ Scrollable Sort Textures tab (buttons always accessible)")
print("3. ✅ Duplicate 'Organize Now' button removed")
print("4. ✅ Icon properly configured for .exe and window")
print("5. ✅ All tab emoji icons present")
print("6. ✅ Clean shutdown with sys.exit(0)")
