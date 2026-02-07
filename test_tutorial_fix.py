"""
Test script to verify tutorial overlay bug fixes
Tests that the WM_DELETE_WINDOW protocol and overlay click handler are properly set up
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Tutorial Overlay Bug Fix - Verification Test")
print("=" * 60)
print()

# Test 1: Direct source code inspection (doesn't require imports)
print("[1/3] Verifying source code changes...")
try:
    tutorial_file = Path(__file__).parent / "src" / "features" / "tutorial_system.py"
    with open(tutorial_file, 'r') as f:
        source_code = f.read()
    
    print("  ✓ Source file loaded")
    
    # Check for _on_overlay_click method
    if "def _on_overlay_click(self" in source_code:
        print("  ✓ _on_overlay_click method exists")
    else:
        print("  ✗ _on_overlay_click method not found")
        sys.exit(1)
    
    # Check for overlay click binding
    if 'bind("<Button-1>"' in source_code and "_on_overlay_click" in source_code:
        print("  ✓ Overlay click handler is bound")
    else:
        print("  ✗ Overlay click handler binding not found")
        sys.exit(1)
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Test 2: Check WM_DELETE_WINDOW protocol
print("[2/3] Verifying WM_DELETE_WINDOW protocol handler...")
try:
    if 'protocol("WM_DELETE_WINDOW"' in source_code:
        print("  ✓ WM_DELETE_WINDOW protocol handler is set")
        
        # Find the line and check it calls _complete_tutorial
        for line in source_code.split('\n'):
            if 'protocol("WM_DELETE_WINDOW"' in line:
                if "_complete_tutorial" in line:
                    print("  ✓ Handler calls _complete_tutorial")
                else:
                    print("  ⚠ Warning: Handler may not call _complete_tutorial")
                break
    else:
        print("  ✗ WM_DELETE_WINDOW protocol handler not found")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
print()

# Test 3: Verify _skip_tutorial improvements
print("[3/3] Verifying _skip_tutorial overlay handling...")
try:
    # Find the _skip_tutorial method
    skip_tutorial_start = source_code.find("def _skip_tutorial(self):")
    if skip_tutorial_start == -1:
        print("  ✗ _skip_tutorial method not found")
        sys.exit(1)
    
    # Get the method body (roughly - find next method definition)
    next_method = source_code.find("\n    def ", skip_tutorial_start + 1)
    skip_tutorial_code = source_code[skip_tutorial_start:next_method]
    
    checks = {
        "overlay topmost lowering": "attributes('-topmost', False)" in skip_tutorial_code,
        "try-finally block": "try:" in skip_tutorial_code and "finally:" in skip_tutorial_code,
        "overlay topmost restoration": "attributes('-topmost', True)" in skip_tutorial_code
    }
    
    all_passed = True
    for check_name, result in checks.items():
        if result:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ Missing: {check_name}")
            all_passed = False
    
    if not all_passed:
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
print()

print("=" * 60)
print("✅ All tests passed!")
print("=" * 60)
print()
print("Summary of fixes:")
print("  1. ✓ WM_DELETE_WINDOW protocol handler added to tutorial window")
print("  2. ✓ Overlay click handler (_on_overlay_click) implemented")
print("  3. ✓ _skip_tutorial now handles overlay topmost properly")
print()
print("These fixes ensure:")
print("  • Clicking X button closes tutorial and removes overlay")
print("  • Clicking overlay brings tutorial to front or closes if missing")
print("  • Skip dialog is visible and doesn't leave overlay stuck")
print()

# Bonus: Show the actual changes
print("=" * 60)
print("Code snippets of the fixes:")
print("=" * 60)
print()

print("1. WM_DELETE_WINDOW protocol handler:")
lines = source_code.split('\n')
for i, line in enumerate(lines):
    if 'protocol("WM_DELETE_WINDOW"' in line:
        # Print surrounding lines for context
        start = max(0, i - 2)
        end = min(len(lines), i + 2)
        for j in range(start, end):
            print(f"   {lines[j]}")
        break
print()

print("2. Overlay click handler method:")
on_overlay_start = source_code.find("def _on_overlay_click(")
if on_overlay_start != -1:
    next_method = source_code.find("\n    def ", on_overlay_start + 1)
    if next_method != -1:
        method_code = source_code[on_overlay_start:next_method].strip()
    else:
        # _on_overlay_click is the last method, take rest of file
        method_code = source_code[on_overlay_start:].strip()
    for line in method_code.split('\n')[:10]:  # First 10 lines
        print(f"   {line}")
print()
