#!/usr/bin/env python3
"""
Test Qt Panel Integration - Verify Qt panels are actually being used
"""
import sys
import os

def test_qt_panels_exist():
    """Test that Qt panel files exist"""
    qt_panels = [
        'src/ui/batch_normalizer_panel_qt.py',
        'src/ui/quality_checker_panel_qt.py',
        'src/ui/color_correction_panel_qt.py',
        'src/ui/background_remover_panel_qt.py',
        'src/ui/alpha_fixer_panel_qt.py',
    ]
    
    missing = []
    for panel in qt_panels:
        if not os.path.exists(panel):
            missing.append(panel)
    
    if missing:
        print(f"❌ Missing Qt panels: {missing}")
        return False
    
    print(f"✅ All {len(qt_panels)} Qt panel files exist")
    return True


def test_main_imports_qt():
    """Test that main.py tries to import Qt versions"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    expected_imports = [
        'batch_normalizer_panel_qt',
        'quality_checker_panel_qt',
        'color_correction_panel_qt',
        'background_remover_panel_qt',
    ]
    
    missing = []
    for imp in expected_imports:
        if imp not in content:
            missing.append(imp)
    
    if missing:
        print(f"❌ main.py doesn't import Qt versions: {missing}")
        return False
    
    print(f"✅ main.py imports all {len(expected_imports)} Qt panel versions")
    return True


def test_qt_flags_exist():
    """Test that main.py has flags for Qt panel tracking"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    expected_flags = [
        'BATCH_NORMALIZER_IS_QT',
        'QUALITY_CHECKER_IS_QT',
        'COLOR_CORRECTION_IS_QT',
        'BACKGROUND_REMOVER_IS_QT',
    ]
    
    missing = []
    for flag in expected_flags:
        if flag not in content:
            missing.append(flag)
    
    if missing:
        print(f"❌ main.py missing Qt tracking flags: {missing}")
        return False
    
    print(f"✅ main.py has all {len(expected_flags)} Qt tracking flags")
    return True


def test_no_after_in_qt_panels():
    """Test that Qt panels don't use .after() calls (checking actual code, not comments)"""
    import re
    qt_panels = [
        'src/ui/batch_normalizer_panel_qt.py',
        'src/ui/quality_checker_panel_qt.py',
        'src/ui/color_correction_panel_qt.py',
        'src/ui/background_remover_panel_qt.py',
    ]
    
    panels_with_after = []
    for panel in qt_panels:
        if os.path.exists(panel):
            with open(panel, 'r') as f:
                in_docstring = False
                for line in f:
                    # Skip docstrings
                    if '"""' in line or "'''" in line:
                        in_docstring = not in_docstring
                        continue
                    if in_docstring:
                        continue
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    # Check for actual .after( method calls
                    if re.search(r'\.after\s*\(', line):
                        panels_with_after.append(panel)
                        print(f"  Found .after( in {panel}: {line.strip()}")
                        break
    
    if panels_with_after:
        print(f"❌ Qt panels still using .after(): {panels_with_after}")
        return False
    
    print(f"✅ All Qt panels are free of .after() calls")
    return True


def test_qt_panels_use_qthread():
    """Test that Qt panels use QThread"""
    qt_panels = [
        'src/ui/batch_normalizer_panel_qt.py',
        'src/ui/quality_checker_panel_qt.py',
        'src/ui/color_correction_panel_qt.py',
    ]
    
    panels_without_qthread = []
    for panel in qt_panels:
        if os.path.exists(panel):
            with open(panel, 'r') as f:
                content = f.read()
                if 'QThread' not in content:
                    panels_without_qthread.append(panel)
    
    if panels_without_qthread:
        print(f"❌ Qt panels not using QThread: {panels_without_qthread}")
        return False
    
    print(f"✅ All major Qt panels use QThread for background work")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Qt Panel Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Qt panel files exist", test_qt_panels_exist),
        ("main.py imports Qt versions", test_main_imports_qt),
        ("Qt tracking flags exist", test_qt_flags_exist),
        ("Qt panels don't use .after()", test_no_after_in_qt_panels),
        ("Qt panels use QThread", test_qt_panels_use_qthread),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
