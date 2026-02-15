#!/usr/bin/env python3
"""
Simple test to verify new widget modules are syntactically correct.
"""

import sys
import ast

def test_file(filepath):
    """Test if a Python file is syntactically valid"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        print(f"✓ {filepath} - Syntax OK")
        return True
    except SyntaxError as e:
        print(f"✗ {filepath} - Syntax Error: {e}")
        return False

if __name__ == "__main__":
    files = [
        "src/ui/achievement_display_simple.py",
        "src/ui/enemy_display_simple.py",
        "src/ui/travel_animation_simple.py",
    ]
    
    all_ok = True
    for f in files:
        if not test_file(f):
            all_ok = False
    
    if all_ok:
        print("\n✓ All new widget files are syntactically correct!")
        sys.exit(0)
    else:
        print("\n✗ Some files have syntax errors")
        sys.exit(1)
