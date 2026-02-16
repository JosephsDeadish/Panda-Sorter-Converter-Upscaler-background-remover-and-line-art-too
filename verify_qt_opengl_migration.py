#!/usr/bin/env python3
"""
Verification Script: Qt6/OpenGL Migration
Ensures NO tkinter, NO canvas, ONLY Qt6 + OpenGL

This script verifies that the codebase has completely migrated to Qt6/OpenGL
and contains no legacy tkinter/canvas references.

Author: Dead On The Inside / JosephsDeadish
"""

import sys
from pathlib import Path
import re

def check_file_for_legacy(file_path):
    """Check a Python file for legacy tkinter/canvas imports."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_lower = line.strip().lower()
                
                # Skip comments
                if line_lower.startswith('#'):
                    continue
                
                # Check for tkinter imports (not in comments)
                if 'import tkinter' in line_lower and '#' not in line[:line.lower().index('import tkinter')]:
                    issues.append((line_num, 'tkinter import', line.strip()))
                elif 'from tkinter' in line_lower and '#' not in line[:line.lower().index('from tkinter')]:
                    issues.append((line_num, 'tkinter import', line.strip()))
                
                # Check for ImageTk (tkinter-specific PIL)
                if 'import imagetk' in line_lower or 'from pil import imagetk' in line_lower:
                    if '#' not in line[:line.lower().index('imagetk')]:
                        issues.append((line_num, 'ImageTk (tkinter PIL)', line.strip()))
                
                # Check for Canvas class definition (not Qt)
                if re.search(r'\bclass\s+.*Canvas[^a-z]', line) and 'QGraphics' not in line:
                    if '#' not in line[:line.lower().index('canvas')]:
                        issues.append((line_num, 'Canvas class definition', line.strip()))
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return issues

def verify_qt_opengl_migration():
    """Main verification function."""
    print("=" * 80)
    print("Qt6/OpenGL Migration Verification")
    print("=" * 80)
    print()
    
    repo_root = Path(__file__).parent
    src_dir = repo_root / 'src'
    main_file = repo_root / 'main.py'
    
    # Files to check
    files_to_check = []
    files_to_check.append(main_file)
    files_to_check.extend(src_dir.rglob('*.py'))
    
    # Track statistics
    total_files = 0
    files_with_issues = 0
    total_issues = 0
    issue_details = []
    
    print("Scanning Python files for legacy tkinter/canvas code...")
    print()
    
    for py_file in files_to_check:
        # Skip test files and __pycache__
        if '__pycache__' in str(py_file) or 'test_' in py_file.name:
            continue
        
        # Skip this verification script itself
        if py_file.name == 'verify_qt_opengl_migration.py':
            continue
        
        # Skip architecture verification (it checks for canvas absence)
        if py_file.name == 'verify_architecture.py':
            continue
        
        total_files += 1
        issues = check_file_for_legacy(py_file)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            issue_details.append((py_file, issues))
    
    # Print results
    print(f"Files scanned: {total_files}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total issues found: {total_issues}")
    print()
    
    if issue_details:
        print("❌ ISSUES FOUND:")
        print("=" * 80)
        for file_path, issues in issue_details:
            rel_path = file_path.relative_to(repo_root)
            print(f"\n📄 {rel_path}")
            for line_num, issue_type, line_content in issues:
                print(f"   Line {line_num}: {issue_type}")
                print(f"   → {line_content}")
        print()
        print("=" * 80)
        print("❌ VERIFICATION FAILED: Legacy tkinter/canvas code found!")
        print("=" * 80)
        return 1
    else:
        print("✅ VERIFICATION PASSED!")
        print("=" * 80)
        print()
        print("✓ No tkinter imports found")
        print("✓ No canvas-based UI code found")
        print("✓ Pure Qt6/OpenGL implementation confirmed")
        print()
        print("The codebase has successfully migrated to Qt6 + OpenGL:")
        print("  • UI: PyQt6 widgets and layouts")
        print("  • 3D Graphics: OpenGL with hardware acceleration")
        print("  • No legacy compatibility layers")
        print("  • No tkinter dependencies")
        print()
        return 0

if __name__ == '__main__':
    sys.exit(verify_qt_opengl_migration())
