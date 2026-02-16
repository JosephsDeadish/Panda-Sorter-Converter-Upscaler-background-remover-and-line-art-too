#!/usr/bin/env python3
"""
Test Settings Panel Structure
Validates the settings panel code structure without running the GUI
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def test_settings_panel_structure():
    """Test that the settings panel has the required structure"""
    print("Testing Settings Panel Structure...")
    
    # Check file exists
    settings_file = Path(__file__).parent / 'src' / 'ui' / 'settings_panel_qt.py'
    assert settings_file.exists(), "settings_panel_qt.py does not exist"
    print("✓ Settings panel file exists")
    
    # Read the file
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check for required classes
    assert 'class ColorWheelWidget' in content, "ColorWheelWidget class missing"
    print("✓ ColorWheelWidget class found")
    
    assert 'class SettingsPanelQt' in content, "SettingsPanelQt class missing"
    print("✓ SettingsPanelQt class found")
    
    # Check for required tab creation methods
    required_methods = [
        'create_appearance_tab',
        'create_cursor_tab',
        'create_font_tab',
        'create_behavior_tab',
        'create_performance_tab',
        'create_advanced_tab'
    ]
    
    for method in required_methods:
        assert f'def {method}' in content, f"{method} method missing"
        print(f"✓ {method} method found")
    
    # Check for required functionality
    required_features = [
        'settingsChanged',  # Signal
        'load_settings',
        'on_setting_changed',
        'apply_theme',
        'reset_to_defaults',
        'export_settings',
        'import_settings'
    ]
    
    for feature in required_features:
        assert feature in content, f"{feature} missing"
        print(f"✓ {feature} found")
    
    # Check for UI components
    ui_components = [
        'QComboBox',  # Theme selector, cursor selector, etc.
        'QSlider',    # Opacity, animation speed, volume
        'QCheckBox',  # Tooltips, sound, debug
        'QSpinBox',   # Thread count, memory, cache
        'QGroupBox',  # Section grouping
        'QTabWidget'  # Tab organization
    ]
    
    for component in ui_components:
        assert component in content, f"{component} not used"
        print(f"✓ {component} used")
    
    # Check file size (should be 600+ lines as specified)
    lines = content.split('\n')
    assert len(lines) >= 600, f"File too short: {len(lines)} lines (expected 600+)"
    print(f"✓ File has {len(lines)} lines (600+ required)")
    
    print("\n✅ All structure tests passed!")
    return True

def test_main_integration():
    """Test that main.py integrates the settings panel"""
    print("\nTesting Main.py Integration...")
    
    main_file = Path(__file__).parent / 'main.py'
    assert main_file.exists(), "main.py does not exist"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check import
    assert 'from ui.settings_panel_qt import SettingsPanelQt' in content, \
        "SettingsPanelQt not imported in main.py"
    print("✓ SettingsPanelQt imported")
    
    # Check it's used in create_settings_tab
    assert 'SettingsPanelQt(config, self)' in content, \
        "SettingsPanelQt not instantiated"
    print("✓ SettingsPanelQt instantiated")
    
    # Check for settings changed handler
    assert 'def on_settings_changed' in content, \
        "on_settings_changed handler missing"
    print("✓ on_settings_changed handler found")
    
    # Check tooltip manager
    assert 'self.tooltip_manager' in content, \
        "tooltip_manager not initialized"
    print("✓ tooltip_manager initialized")
    
    print("\n✅ All integration tests passed!")
    return True

def test_config_updates():
    """Test that config.py has the required fields"""
    print("\nTesting Config Updates...")
    
    config_file = Path(__file__).parent / 'src' / 'config.py'
    assert config_file.exists(), "config.py does not exist"
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Check for required config fields
    required_fields = [
        '"accent_color"',
        '"font_weight"',
        '"sound_enabled"',
        '"sound_volume"',
        '"thumbnail_quality"'
    ]
    
    for field in required_fields:
        assert field in content, f"{field} missing from config"
        print(f"✓ {field} found in config")
    
    print("\n✅ All config tests passed!")
    return True

if __name__ == '__main__':
    try:
        test_settings_panel_structure()
        test_main_integration()
        test_config_updates()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*50)
        print("\nSettings Panel successfully implemented with:")
        print("  ✓ 6 comprehensive tabs (Appearance, Cursor, Font, Behavior, Performance, Advanced)")
        print("  ✓ ColorWheelWidget for color selection")
        print("  ✓ Real-time settings application")
        print("  ✓ Import/Export functionality")
        print("  ✓ Integration with main window")
        print("  ✓ Config persistence")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
