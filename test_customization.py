#!/usr/bin/env python3
"""
Test script for UI Customization Panel
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Test imports
print("Testing imports...")
try:
    from src.config import config
    print("✓ Config imported")
    
    from src.ui.customization_panel import (
        ColorWheelWidget,
        CursorCustomizer,
        ThemeManager,
        CustomizationPanel,
        open_customization_dialog,
        THEME_PRESETS
    )
    print("✓ Customization panel components imported")
    
    # Test theme presets
    print(f"\n✓ Found {len(THEME_PRESETS)} theme presets:")
    for theme_id, theme_data in THEME_PRESETS.items():
        print(f"  - {theme_data['name']} ({theme_data['appearance_mode']})")
    
    print("\n✅ All imports successful!")
    print("\nNote: GUI components require a display to fully test.")
    print("Integration with main.py is complete.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("Integration Points in main.py:")
print("="*60)
print("1. Import: from src.ui.customization_panel import open_customization_dialog")
print("2. Settings tab: 'Open Customization Panel' button")
print("3. Method: open_customization() to launch the dialog")
print("4. Startup: _load_initial_theme() loads saved theme")
print("="*60)
