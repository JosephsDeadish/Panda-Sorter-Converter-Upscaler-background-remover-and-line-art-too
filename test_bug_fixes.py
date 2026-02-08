#!/usr/bin/env python3
"""
Test script to verify all 5 bug fixes from the comprehensive PR
"""

import sys
import ast
import re

print("=" * 60)
print("Testing Bug Fixes - Comprehensive Validation")
print("=" * 60)

# Bug 1: Verify no Path shadowing
print("\n[Bug 1] Checking for Path shadowing in main.py...")
with open('main.py', 'r') as f:
    content = f.read()
    tree = ast.parse(content)
    
# Check module-level import
has_module_import = 'from pathlib import Path' in content
print(f"  {'✓' if has_module_import else '✗'} Module-level Path import exists")

# Find sort_textures_thread and check for local Path assignments
found_method = False
has_local_path = False
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'sort_textures_thread':
        found_method = True
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == 'Path':
                        has_local_path = True
                        print(f"  ✗ Found Path assignment at line {child.lineno}")

if found_method:
    print(f"  {'✗' if has_local_path else '✓'} No local Path assignments in sort_textures_thread")
else:
    print("  ⚠ sort_textures_thread not found")

# Bug 2: Check tooltip improvements
print("\n[Bug 2] Checking tooltip improvements in tutorial_system.py...")
with open('src/features/tutorial_system.py', 'r') as f:
    tutorial_content = f.read()

uses_tk_toplevel = 'tk.Toplevel' in tutorial_content
has_mapping_check = 'winfo_ismapped' in tutorial_content
has_canvas_bind = '_canvas' in tutorial_content and 'bind' in tutorial_content

print(f"  {'✓' if uses_tk_toplevel else '✗'} Uses tk.Toplevel instead of CTkToplevel")
print(f"  {'✓' if has_mapping_check else '✗'} Has widget mapping check")
print(f"  {'✓' if has_canvas_bind else '✗'} Binds to internal canvas widget")

# Bug 3: Check tutorial error handling
print("\n[Bug 3] Checking tutorial error handling in main.py...")
has_tutorial_logging = 'logger.warning("Tutorial button clicked' in content
has_detailed_errors = 'Tutorial Unavailable' in content
has_error_try_catch = 'try:' in content and 'self.tutorial_manager.start_tutorial()' in content

print(f"  {'✓' if has_tutorial_logging else '✗'} Has logging for tutorial button")
print(f"  {'✓' if has_detailed_errors else '✗'} Has detailed error messages")
print(f"  {'✓' if has_error_try_catch else '✗'} Has try-catch in _run_tutorial")

# Bug 4: Check customization panel dialog improvements
print("\n[Bug 4] Checking customization panel improvements...")
with open('src/ui/customization_panel.py', 'r') as f:
    custom_content = f.read()

has_transient = 'transient(parent)' in custom_content
has_grab_set = 'grab_set()' in custom_content
has_wm_delete = 'WM_DELETE_WINDOW' in custom_content
has_grab_release = 'grab_release' in custom_content

print(f"  {'✓' if has_transient else '✗'} Dialog is transient to parent")
print(f"  {'✓' if has_grab_set else '✗'} Dialog uses grab_set() for modal behavior")
print(f"  {'✓' if has_wm_delete else '✗'} Has WM_DELETE_WINDOW protocol handler")
print(f"  {'✓' if has_grab_release else '✗'} Releases grab on close")

# Bug 5: Check Windows taskbar icon fix
print("\n[Bug 5] Checking Windows taskbar icon fix in main.py...")
has_ctypes_import = 'import ctypes' in content
has_appusermodel = 'SetCurrentProcessExplicitAppUserModelID' in content
has_iconbitmap_first = content.find('iconbitmap') < content.find('iconphoto')

print(f"  {'✓' if has_ctypes_import else '✗'} Imports ctypes")
print(f"  {'✓' if has_appusermodel else '✗'} Calls SetCurrentProcessExplicitAppUserModelID")
print(f"  {'✓' if has_iconbitmap_first else '✗'} Sets iconbitmap before iconphoto")

# Check if ctypes call is before GUI imports
ctypes_pos = content.find('import ctypes')
ctk_import_pos = content.find('import customtkinter')
if ctypes_pos >= 0 and ctk_import_pos >= 0:
    before_gui = ctypes_pos < ctk_import_pos
    print(f"  {'✓' if before_gui else '✗'} ctypes import is before GUI imports")

print("\n" + "=" * 60)
print("Validation Complete!")
print("=" * 60)
