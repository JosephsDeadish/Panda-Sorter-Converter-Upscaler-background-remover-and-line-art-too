#!/usr/bin/env python3
"""Test that files can be parsed without importing CustomTkinter"""

import ast
import sys

def check_syntax(filepath):
    """Check if file has valid Python syntax"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

files_to_check = [
    'src/ui/__init__.py',
    'src/ui/customization_panel.py',
    'main.py',
    'src/config.py'
]

print("Checking Python syntax...")
print("=" * 60)

all_good = True
for filepath in files_to_check:
    valid, error = check_syntax(filepath)
    if valid:
        print(f"✓ {filepath}")
    else:
        print(f"✗ {filepath}: {error}")
        all_good = False

print("=" * 60)

if all_good:
    print("✅ All files have valid syntax!")
    sys.exit(0)
else:
    print("❌ Some files have syntax errors")
    sys.exit(1)
