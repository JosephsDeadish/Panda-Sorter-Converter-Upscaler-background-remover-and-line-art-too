#!/usr/bin/env python3
"""
Comprehensive Integration Verification Script
Checks that all components of the AI Organizer are properly connected
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def check_imports():
    """Verify all required imports work."""
    print("="*60)
    print("CHECKING IMPORTS")
    print("="*60)
    
    results = []
    
    # Critical imports
    try:
        from organizer.learning_system import AILearningSystem, LearningEntry, LearningProfileMetadata
        print("✓ Learning system imports OK")
        results.append(("Learning System", True))
    except Exception as e:
        print(f"✗ Learning system imports FAILED: {e}")
        results.append(("Learning System", False))
    
    try:
        from organizer import OrganizationEngine, ORGANIZATION_STYLES, TextureInfo
        print("✓ Organization engine imports OK")
        results.append(("Organization Engine", True))
    except Exception as e:
        print(f"✗ Organization engine imports FAILED: {e}")
        results.append(("Organization Engine", False))
    
    try:
        from features.game_identifier import GameIdentifier, GameInfo
        print("✓ Game identifier imports OK")
        results.append(("Game Identifier", True))
    except Exception as e:
        print(f"✗ Game identifier imports FAILED: {e}")
        results.append(("Game Identifier", False))
    
    try:
        from features.profile_manager import ProfileManager
        print("✓ Profile manager imports OK")
        results.append(("Profile Manager", True))
    except Exception as e:
        print(f"✗ Profile manager imports FAILED: {e}")
        results.append(("Profile Manager", False))
    
    # Optional imports
    try:
        from vision_models.clip_model import CLIPModel
        print("✓ CLIP model imports OK (optional)")
        results.append(("CLIP Model", True))
    except Exception as e:
        print(f"⚠ CLIP model not available (optional): {e}")
        results.append(("CLIP Model (optional)", None))
    
    try:
        from vision_models.dinov2_model import DINOv2Model
        print("✓ DINOv2 model imports OK (optional)")
        results.append(("DINOv2 Model", True))
    except Exception as e:
        print(f"⚠ DINOv2 model not available (optional): {e}")
        results.append(("DINOv2 Model (optional)", None))
    
    try:
        from utils.archive_handler import ArchiveHandler
        print("✓ Archive handler imports OK")
        results.append(("Archive Handler", True))
    except Exception as e:
        print(f"⚠ Archive handler not available: {e}")
        results.append(("Archive Handler", None))
    
    print()
    return results

def check_main_integration():
    """Check main.py integration."""
    print("="*60)
    print("CHECKING MAIN.PY INTEGRATION")
    print("="*60)
    
    main_file = Path(__file__).parent / 'main.py'
    if not main_file.exists():
        print("✗ main.py not found")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    checks = [
        ("OrganizerPanelQt import", "from ui.organizer_panel_qt import OrganizerPanelQt"),
        ("OrganizerPanel instantiation", "organizer_panel = OrganizerPanelQt()"),
        ("OrganizerPanel added to tabs", 'tool_tabs.addTab(organizer_panel'),
    ]
    
    all_ok = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name} - NOT FOUND")
            all_ok = False
    
    print()
    return all_ok

def check_file_structure():
    """Verify all required files exist."""
    print("="*60)
    print("CHECKING FILE STRUCTURE")
    print("="*60)
    
    required_files = [
        "src/organizer/learning_system.py",
        "src/ui/organizer_panel_qt.py",
        "src/organizer/__init__.py",
        "src/organizer/organization_engine.py",
        "src/organizer/organization_styles.py",
        "src/features/game_identifier.py",
        "src/features/profile_manager.py",
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_ok = False
    
    print()
    return all_ok

def check_tests():
    """Verify test files exist and are valid."""
    print("="*60)
    print("CHECKING TEST FILES")
    print("="*60)
    
    test_files = [
        "test_organizer_learning.py",
        "test_organizer_integration.py",
    ]
    
    all_ok = True
    for test_file in test_files:
        full_path = Path(__file__).parent / test_file
        if full_path.exists():
            print(f"✓ {test_file}")
        else:
            print(f"✗ {test_file} - MISSING")
            all_ok = False
    
    print()
    return all_ok

def check_documentation():
    """Verify documentation exists."""
    print("="*60)
    print("CHECKING DOCUMENTATION")
    print("="*60)
    
    doc_files = [
        "docs/AI_ORGANIZER_GUIDE.md",
        "docs/AI_ORGANIZER_QUICK_START.md",
        "docs/AI_ORGANIZER_UI_LAYOUT.md",
        "ORGANIZER_IMPLEMENTATION_SUMMARY.md",
        "examples/god_of_war_ii_learning_profile.json",
    ]
    
    all_ok = True
    for doc_file in doc_files:
        full_path = Path(__file__).parent / doc_file
        if full_path.exists():
            print(f"✓ {doc_file}")
        else:
            print(f"✗ {doc_file} - MISSING")
            all_ok = False
    
    print()
    return all_ok

def verify_ui_panel():
    """Verify UI panel is properly structured."""
    print("="*60)
    print("VERIFYING UI PANEL STRUCTURE")
    print("="*60)
    
    panel_file = Path(__file__).parent / 'src' / 'ui' / 'organizer_panel_qt.py'
    if not panel_file.exists():
        print("✗ organizer_panel_qt.py not found")
        return False
    
    with open(panel_file, 'r') as f:
        content = f.read()
    
    required_methods = [
        "_create_game_detection_section",
        "_create_mode_selection_section",
        "_create_file_input_section",
        "_create_work_area_section",
        "_create_progress_section",
        "_create_action_buttons",
        "_create_settings_section",
        "_on_good_feedback",
        "_on_bad_feedback",
        "_detect_game",
        "_start_organization",
        "_export_learning_profile",
        "_import_learning_profile",
    ]
    
    all_ok = True
    for method in required_methods:
        if f"def {method}" in content:
            print(f"✓ {method}()")
        else:
            print(f"✗ {method}() - MISSING")
            all_ok = False
    
    print()
    return all_ok

def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("AI ORGANIZER INTEGRATION VERIFICATION")
    print("="*60 + "\n")
    
    results = {}
    
    # Run all checks
    results['imports'] = check_imports()
    results['main_integration'] = check_main_integration()
    results['file_structure'] = check_file_structure()
    results['tests'] = check_tests()
    results['documentation'] = check_documentation()
    results['ui_panel'] = verify_ui_panel()
    
    # Summary
    print("="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    # Count import results
    import_results = results['imports']
    critical_imports = [r for r in import_results if r[1] is not None and "optional" not in r[0].lower()]
    critical_pass = sum(1 for r in critical_imports if r[1] is True)
    critical_total = len(critical_imports)
    
    print(f"Critical Imports: {critical_pass}/{critical_total} passed")
    
    # Other checks
    checks = [
        ("Main.py Integration", results['main_integration']),
        ("File Structure", results['file_structure']),
        ("Test Files", results['tests']),
        ("Documentation", results['documentation']),
        ("UI Panel Structure", results['ui_panel']),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed and critical_pass == critical_total:
        print("\n✅ ALL CHECKS PASSED - SYSTEM READY")
        return 0
    else:
        print("\n⚠️ SOME CHECKS FAILED - REVIEW ABOVE")
        return 1

if __name__ == "__main__":
    sys.exit(main())
