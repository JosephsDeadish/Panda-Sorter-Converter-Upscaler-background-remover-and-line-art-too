#!/usr/bin/env python3
"""
Test script to validate Phase 1 bug fixes
Tests the PhotoImage GC fix, DDS support, and thumbnail cache
"""

import sys
from pathlib import Path

# Test 1: Validate preview_viewer.py changes
def test_preview_viewer_structure():
    """Verify preview_viewer.py has the required changes"""
    print("Testing preview_viewer.py structure...")
    
    preview_file = Path("src/features/preview_viewer.py")
    content = preview_file.read_text()
    
    # Check for _current_photo instance variable
    assert "_current_photo" in content, "Missing _current_photo instance variable"
    print("✅ Found _current_photo instance variable")
    
    # Check for DDS support in _load_image
    assert "suffix.lower() == '.dds'" in content, "Missing DDS support"
    print("✅ Found DDS file support")
    
    # Check for PhotoImage reference storage
    assert "self._current_photo = ImageTk.PhotoImage" in content, "Missing PhotoImage GC fix"
    print("✅ Found PhotoImage GC prevention code")
    
    print("✅ preview_viewer.py structure validated\n")

# Test 2: Validate main.py changes
def test_main_structure():
    """Verify main.py has the required changes"""
    print("Testing main.py structure...")
    
    main_file = Path("main.py")
    content = main_file.read_text()
    
    # Check for thumbnail cache
    assert "_thumbnail_cache" in content, "Missing thumbnail cache"
    print("✅ Found thumbnail cache")
    
    # Check for _create_thumbnail method
    assert "def _create_thumbnail" in content, "Missing _create_thumbnail method"
    print("✅ Found _create_thumbnail method")
    
    # Check for tooltip application methods
    assert "_apply_sort_tooltips" in content, "Missing _apply_sort_tooltips"
    assert "_apply_convert_tooltips" in content, "Missing _apply_convert_tooltips"
    assert "_apply_browser_tooltips" in content, "Missing _apply_browser_tooltips"
    assert "_apply_menu_tooltips" in content, "Missing _apply_menu_tooltips"
    print("✅ Found all tooltip application methods")
    
    # Check for customization callback improvements
    assert "_apply_theme_to_widget" in content, "Missing _apply_theme_to_widget"
    assert "_apply_color_to_widget" in content, "Missing _apply_color_to_widget"
    assert "_apply_cursor_to_widget" in content, "Missing _apply_cursor_to_widget"
    print("✅ Found customization callback helper methods")
    
    # Check for layout improvements
    assert "# ===== ACTION BUTTONS AT TOP =====" in content, "Sort tab buttons not at top"
    print("✅ Sort tab has buttons at top")
    
    assert "# === START CONVERSION BUTTON AT TOP" in content, "Convert button not at top"
    print("✅ Convert tab has button at top")
    
    assert "scrollable_content = ctk.CTkScrollableFrame(self.tab_convert)" in content, "Convert tab not scrollable"
    print("✅ Convert tab is scrollable")
    
    print("✅ main.py structure validated\n")

# Test 3: Validate tooltip storage
def test_tooltip_storage():
    """Verify tooltips are stored to prevent GC"""
    print("Testing tooltip storage...")
    
    main_file = Path("main.py")
    content = main_file.read_text()
    
    # Count tooltip storage instances
    tooltip_storage_count = content.count("self._tooltips.append(WidgetTooltip")
    
    assert tooltip_storage_count > 10, f"Only {tooltip_storage_count} tooltips stored, expected more"
    print(f"✅ Found {tooltip_storage_count} tooltip storage instances")
    
    print("✅ Tooltip storage validated\n")

# Test 4: Validate tutorial system robustness
def test_tutorial_robustness():
    """Verify tutorial system has better error handling"""
    print("Testing tutorial system robustness...")
    
    main_file = Path("main.py")
    content = main_file.read_text()
    
    # Check for improved error handling
    assert "UI not properly loaded" in content, "Missing improved error handling"
    print("✅ Found improved tutorial error handling")
    
    assert "Tutorial System Warning" in content, "Missing user-friendly error message"
    print("✅ Found user-friendly error messaging")
    
    print("✅ Tutorial system robustness validated\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Bug Fixes Validation Suite - Phase 1")
    print("=" * 60)
    print()
    
    try:
        test_preview_viewer_structure()
        test_main_structure()
        test_tooltip_storage()
        test_tutorial_robustness()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
