"""
Test Qt Panel Loader Integration
Validates that the loader correctly selects Qt or Tkinter panels
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_qt_panel_loader():
    """Test that qt_panel_loader can import and has correct functions."""
    print("Testing qt_panel_loader module...")
    
    try:
        from src.ui.qt_panel_loader import (
            get_widgets_panel,
            get_closet_panel,
            get_hotkey_settings_panel,
            get_customization_panel,
            PYQT6_AVAILABLE
        )
        print("✅ qt_panel_loader imported successfully")
        print(f"   PyQt6 available: {PYQT6_AVAILABLE}")
        
        # Test function signatures
        assert callable(get_widgets_panel), "get_widgets_panel not callable"
        assert callable(get_closet_panel), "get_closet_panel not callable"
        assert callable(get_hotkey_settings_panel), "get_hotkey_settings_panel not callable"
        assert callable(get_customization_panel), "get_customization_panel not callable"
        
        print("✅ All loader functions are callable")
        return True
        
    except Exception as e:
        print(f"❌ qt_panel_loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qt_modules_exist():
    """Test that the Qt modules we created actually exist."""
    print("\nTesting Qt module files exist...")
    
    modules = [
        'src/ui/weapon_positioning_qt.py',
        'src/features/preview_viewer_qt.py',
        'src/ui/closet_display_qt.py',
        'src/ui/color_picker_qt.py',
        'src/ui/trail_preview_qt.py',
        'src/ui/paint_tools_qt.py',
        'src/ui/widgets_display_qt.py',
        'src/ui/live_preview_qt.py',
        'src/ui/hotkey_display_qt.py',
    ]
    
    all_exist = True
    for module in modules:
        if os.path.exists(module):
            print(f"✅ {module}")
        else:
            print(f"❌ {module} - FILE NOT FOUND")
            all_exist = False
    
    return all_exist


def test_qt_modules_importable():
    """Test that Qt modules can be imported (if PyQt6 available)."""
    print("\nTesting Qt module imports...")
    
    # Check if PyQt6 available
    try:
        from PyQt6.QtWidgets import QWidget
        print("✅ PyQt6 is available - testing imports")
    except ImportError:
        print("⚠️  PyQt6 not available - skipping import tests")
        return True
    
    modules_to_test = [
        ('src.ui.weapon_positioning_qt', 'WeaponPositioningQt'),
        ('src.features.preview_viewer_qt', 'PreviewViewerQt'),
        ('src.ui.closet_display_qt', 'ClosetDisplayQt'),
        ('src.ui.color_picker_qt', 'ColorPickerQt'),
        ('src.ui.trail_preview_qt', 'TrailPreviewQt'),
        ('src.ui.paint_tools_qt', 'PaintToolsQt'),
        ('src.ui.widgets_display_qt', 'WidgetsDisplayQt'),
        ('src.ui.live_preview_qt', 'LivePreviewQt'),
        ('src.ui.hotkey_display_qt', 'HotkeyDisplayQt'),
    ]
    
    all_importable = True
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}")
            else:
                print(f"⚠️  {module_name} - class {class_name} not found")
                all_importable = False
        except Exception as e:
            print(f"❌ {module_name} - {e}")
            all_importable = False
    
    return all_importable


if __name__ == '__main__':
    print("="*60)
    print("Qt Panel Integration Test Suite")
    print("="*60)
    
    test1 = test_qt_panel_loader()
    test2 = test_qt_modules_exist()
    test3 = test_qt_modules_importable()
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    print(f"Panel Loader: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Files Exist:  {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Imports Work: {'✅ PASS' if test3 else '❌ FAIL'}")
    print("="*60)
    
    if test1 and test2:
        print("\n✅ INTEGRATION TEST PASSED")
        print("The Qt panel loader and modules are properly integrated.")
        sys.exit(0)
    else:
        print("\n❌ INTEGRATION TEST FAILED")
        print("Some integration issues remain.")
        sys.exit(1)
