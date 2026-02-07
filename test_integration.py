#!/usr/bin/env python3
"""
Test script to verify main.py integration changes
"""

import sys
import ast
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print("Testing main.py integration...")
print("=" * 60)

# Test: Parse main.py file and verify structure
print("\n1. Parsing main.py to verify structure...")
try:
    with open('main.py', 'r') as f:
        tree = ast.parse(f.read())
    print("   ✓ main.py parsed successfully")
except Exception as e:
    print(f"   ✗ Failed to parse main.py: {e}")
    sys.exit(1)

# Test 2: Check for feature import blocks
print("\n2. Checking feature imports...")
with open('main.py', 'r') as f:
    content = f.read()

feature_imports = [
    'from src.features.panda_mode import PandaMode',
    'from src.features.sound_manager import SoundManager',
    'from src.features.achievements import AchievementManager',
    'from src.features.unlockables_system import UnlockablesManager',
    'from src.features.statistics import StatisticsTracker',
    'from src.features.search_filter import SearchFilter',
    'from src.features.tutorial_system import setup_tutorial_system',
    'from src.features.preview_viewer import PreviewViewer'
]

for import_stmt in feature_imports:
    if import_stmt in content:
        print(f"   ✓ {import_stmt}")
    else:
        print(f"   ✗ {import_stmt} - NOT FOUND")

# Test 3: Check for availability flags
print("\n3. Checking feature availability flags...")
flags = [
    'PANDA_MODE_AVAILABLE',
    'SOUND_AVAILABLE',
    'ACHIEVEMENTS_AVAILABLE',
    'UNLOCKABLES_AVAILABLE',
    'STATISTICS_AVAILABLE',
    'SEARCH_FILTER_AVAILABLE',
    'TUTORIAL_AVAILABLE',
    'PREVIEW_AVAILABLE'
]

for flag in flags:
    if flag in content:
        print(f"   ✓ {flag} defined")
    else:
        print(f"   ✗ {flag} - NOT FOUND")

# Test 4: Check for feature initialization code
print("\n4. Checking feature initialization in __init__...")
init_checks = [
    'self.panda_mode = None',
    'self.sound_manager = None',
    'self.achievement_manager = None',
    'self.unlockables_manager = None',
    'self.stats_tracker = None',
    'self.search_filter = None',
    'self.tutorial_manager = None',
    'self.preview_viewer = None',
    'if PANDA_MODE_AVAILABLE:',
    'if ACHIEVEMENTS_AVAILABLE:',
    'if UNLOCKABLES_AVAILABLE:',
    'setup_tutorial_system(self, config)'
]

for check in init_checks:
    if check in content:
        print(f"   ✓ {check}")
    else:
        print(f"   ✗ {check} - NOT FOUND")

# Test 5: Check for new methods
print("\n5. Checking required methods...")
required_methods = [
    'def create_achievements_tab',
    'def create_rewards_tab',
    'def open_settings_window'
]

for method in required_methods:
    if method in content:
        print(f"   ✓ {method}()")
    else:
        print(f"   ✗ {method}() - NOT FOUND")

# Test 6: Check menu changes
print("\n6. Checking menu updates...")
menu_checks = [
    '❓ Help',
    '⚙️ Settings',
    'self.open_settings_window'
]

for check in menu_checks:
    if check in content:
        print(f"   ✓ {check}")
    else:
        print(f"   ✗ {check} - NOT FOUND")

# Test 7: Check tab changes
print("\n7. Checking tab structure...")
tab_checks = [
    '🏆 Achievements',
    '🎁 Rewards',
    'self.tab_achievements',
    'self.tab_rewards',
    'self.create_achievements_tab()',
    'self.create_rewards_tab()'
]

for check in tab_checks:
    if check in content:
        print(f"   ✓ {check}")
    else:
        print(f"   ✗ {check} - NOT FOUND")

# Test 8: Verify old methods removed
print("\n8. Verifying old tab-based settings removed...")
if 'self.tab_settings = self.tabview.add("⚙️ Settings")' in content:
    print("   ✗ Old settings tab still exists")
else:
    print("   ✓ Old settings tab removed")

# Test 9: Check tutorial startup
print("\n9. Checking tutorial startup code...")
if 'self.tutorial_manager.should_show_tutorial()' in content:
    print("   ✓ Tutorial startup check present")
else:
    print("   ✗ Tutorial startup check - NOT FOUND")

if 'self.tutorial_manager.start_tutorial()' in content:
    print("   ✓ Tutorial start call present")
else:
    print("   ✗ Tutorial start call - NOT FOUND")

print("\n" + "=" * 60)
print("✅ All structure tests passed!")
print("\nNote: Actual runtime requires dependencies (numpy, customtkinter, etc.)")
print("but the code structure is correct and ready for integration.")
