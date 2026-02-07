"""
Test script to verify the application can start without import errors
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_imports():
    """Test all critical imports"""
    print("Testing PS2 Texture Sorter imports...\n")
    
    errors = []
    
    # Test config
    try:
        from src.config import config, APP_NAME, APP_VERSION, APP_AUTHOR
        print(f"✓ Config OK - {APP_NAME} v{APP_VERSION}")
    except Exception as e:
        errors.append(f"Config: {e}")
        print(f"✗ Config failed: {e}")
    
    # Test organizer (this was the failing import)
    try:
        from src.organizer import OrganizationEngine, ORGANIZATION_STYLES, TextureInfo
        print(f"✓ Organizer OK - {len(ORGANIZATION_STYLES)} styles, TextureInfo class available")
    except Exception as e:
        errors.append(f"Organizer: {e}")
        print(f"✗ Organizer failed: {e}")
    
    # Test classifier
    try:
        from src.classifier import TextureClassifier, ALL_CATEGORIES
        print(f"✓ Classifier OK - {len(ALL_CATEGORIES)} categories")
    except Exception as e:
        errors.append(f"Classifier: {e}")
        print(f"✗ Classifier failed (optional): {e}")
    
    # Test LOD detector
    try:
        from src.lod_detector import LODDetector
        print("✓ LOD Detector OK")
    except Exception as e:
        errors.append(f"LOD Detector: {e}")
        print(f"✗ LOD Detector failed: {e}")
    
    # Test file handler
    try:
        from src.file_handler import FileHandler
        print("✓ File Handler OK")
    except Exception as e:
        errors.append(f"File Handler: {e}")
        print(f"✗ File Handler failed (optional): {e}")
    
    # Test database
    try:
        from src.database import TextureDatabase
        print("✓ Database OK")
    except Exception as e:
        errors.append(f"Database: {e}")
        print(f"✗ Database failed: {e}")
    
    # Test UI customization
    try:
        from src.ui.customization_panel import open_customization_dialog
        print("✓ UI Customization OK")
    except Exception as e:
        print(f"⚠ UI Customization not available (optional): {e}")
    
    # Test panda mode
    try:
        from src.features.panda_mode import PandaMode
        print("✓ Panda Mode OK")
    except Exception as e:
        print(f"⚠ Panda Mode not available (optional): {e}")
    
    # Test unlockables
    try:
        from src.features.unlockables_system import UnlockablesSystem
        print("✓ Unlockables System OK")
    except Exception as e:
        print(f"⚠ Unlockables not available (optional): {e}")
    
    print("\n" + "="*60)
    if errors:
        print(f"CRITICAL ERRORS: {len(errors)}")
        for err in errors:
            print(f"  - {err}")
        print("\nPlease install dependencies: pip install -r requirements.txt")
        return False
    else:
        print("SUCCESS: All critical imports working!")
        print("Application should start without import errors.")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
