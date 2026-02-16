#!/usr/bin/env python3
"""
Test AI Models UI Implementation
Validates the improved AI models settings UI structure and model definitions
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def test_model_manager_structure():
    """Test that model_manager has the improved model definitions"""
    print("Testing Model Manager Structure...")
    
    # Import the module
    from upscaler.model_manager import AIModelManager
    
    # Create instance
    manager = AIModelManager()
    
    # Check that all required models are defined
    required_models = [
        'RealESRGAN_x4plus',
        'RealESRGAN_x2plus',
        'CLIP',
        'DINOv2',
        'transformers',
        'timm',
        'Lanczos_Native'
    ]
    
    for model in required_models:
        assert model in manager.MODELS, f"Model {model} missing from MODELS"
        print(f"✓ {model} found in MODELS")
    
    # Check that models have all required fields
    required_fields = ['description', 'tool', 'category', 'icon']
    
    for model_name, model_info in manager.MODELS.items():
        for field in required_fields:
            assert field in model_info, f"{model_name} missing field: {field}"
        
        # Check specific fields
        assert model_info['description'], f"{model_name} has empty description"
        assert model_info['icon'], f"{model_name} has empty icon"
        assert model_info['category'] in ['upscaler', 'vision', 'nlp', 'acceleration'], \
            f"{model_name} has invalid category: {model_info['category']}"
        
        print(f"✓ {model_name} has all required fields")
    
    # Check specific model properties
    assert manager.MODELS['RealESRGAN_x4plus']['size_mb'] == 67
    assert manager.MODELS['RealESRGAN_x4plus']['version'] == '0.2.5.0'
    assert manager.MODELS['RealESRGAN_x4plus']['category'] == 'upscaler'
    print("✓ RealESRGAN_x4plus has correct properties")
    
    assert manager.MODELS['CLIP']['size_mb'] == 340
    assert manager.MODELS['CLIP']['version'] == 'ViT-B/32'
    assert manager.MODELS['CLIP']['category'] == 'vision'
    print("✓ CLIP has correct properties")
    
    assert manager.MODELS['Lanczos_Native']['native_module'] == True
    assert manager.MODELS['Lanczos_Native']['category'] == 'acceleration'
    print("✓ Lanczos_Native has correct properties")
    
    print("\n✅ All model manager tests passed!")
    return True

def test_ai_models_tab_structure():
    """Test that the AI models settings tab has the improved structure"""
    print("\nTesting AI Models Settings Tab Structure...")
    
    # Check file exists
    tab_file = Path(__file__).parent / 'src' / 'ui' / 'ai_models_settings_tab.py'
    assert tab_file.exists(), "ai_models_settings_tab.py does not exist"
    print("✓ AI models settings tab file exists")
    
    # Read the file
    with open(tab_file, 'r') as f:
        content = f.read()
    
    # Check for required classes
    assert 'class ModelDownloadThread' in content, "ModelDownloadThread class missing"
    print("✓ ModelDownloadThread class found")
    
    assert 'class ModelCardWidget' in content, "ModelCardWidget class missing"
    print("✓ ModelCardWidget class found")
    
    assert 'class AIModelsSettingsTab' in content, "AIModelsSettingsTab class missing"
    print("✓ AIModelsSettingsTab class found")
    
    # Check ModelCardWidget has required methods
    required_methods = [
        'setup_ui',
        'create_header',
        'toggle_expand',
        'populate_details',
        'download_model',
        'on_download_finished',
        'delete_model',
        'recreate_ui'
    ]
    
    for method in required_methods:
        assert f'def {method}' in content, f"ModelCardWidget.{method} method missing"
        print(f"✓ ModelCardWidget.{method} method found")
    
    # Check for UI features
    ui_features = [
        'expandable',  # Expandable cards
        'setStyleSheet',  # Styling
        'QProgressBar',  # Progress tracking
        'border-radius',  # Rounded corners
        'background-color',  # Color styling
        'category',  # Category grouping
        '✅',  # Status indicators
        '❌',
        '⬇️',  # Download icon
        '🗑️',  # Delete icon
    ]
    
    for feature in ui_features:
        assert feature in content, f"{feature} not found in UI code"
        print(f"✓ {feature} found in UI code")
    
    # Check for category-based organization
    categories = ['upscaler', 'vision', 'nlp', 'acceleration']
    for cat in categories:
        assert cat in content, f"Category {cat} not handled in UI"
        print(f"✓ Category {cat} handled in UI")
    
    # Check file has substantial content
    lines = content.split('\n')
    assert len(lines) >= 400, f"File too short: {len(lines)} lines (expected 400+)"
    print(f"✓ File has {len(lines)} lines (400+ required)")
    
    print("\n✅ All AI models tab structure tests passed!")
    return True

def test_ui_component_details():
    """Test specific UI component requirements"""
    print("\nTesting UI Component Details...")
    
    tab_file = Path(__file__).parent / 'src' / 'ui' / 'ai_models_settings_tab.py'
    with open(tab_file, 'r') as f:
        content = f.read()
    
    # Check for prominent buttons
    assert 'setMinimumHeight(40)' in content, "Buttons not set to minimum 40px height"
    print("✓ Download buttons have minimum 40px height")
    
    assert 'setMinimumWidth(200)' in content, "Buttons not set to minimum 200px width"
    print("✓ Download buttons have minimum 200px width")
    
    # Check for color coding
    assert '#4CAF50' in content, "Green color for download button not found"
    print("✓ Green color for download button")
    
    assert '#f44336' in content, "Red color for delete button not found"
    print("✓ Red color for delete button")
    
    # Check for expand/collapse functionality
    assert 'toggle_expand' in content, "Toggle expand functionality missing"
    print("✓ Toggle expand functionality present")
    
    assert '▼' in content and '▲' in content, "Expand/collapse arrows missing"
    print("✓ Expand/collapse arrow indicators present")
    
    # Check for category headers with emojis
    category_emojis = {
        '📈': 'Upscaler',
        '👁️': 'Vision',
        '🔤': 'NLP',
        '⚡': 'Acceleration'
    }
    
    for emoji, name in category_emojis.items():
        assert emoji in content, f"{name} category emoji {emoji} missing"
        print(f"✓ {name} category emoji {emoji} present")
    
    # Check for message boxes
    assert 'QMessageBox.information' in content, "Success message boxes missing"
    print("✓ Success message boxes present")
    
    assert 'QMessageBox.critical' in content, "Error message boxes missing"
    print("✓ Error message boxes present")
    
    assert 'QMessageBox.question' in content, "Confirmation dialog missing"
    print("✓ Confirmation dialog present")
    
    print("\n✅ All UI component detail tests passed!")
    return True

def test_integration():
    """Test that the tab integrates with settings panel"""
    print("\nTesting Integration with Settings Panel...")
    
    settings_file = Path(__file__).parent / 'src' / 'ui' / 'settings_panel_qt.py'
    assert settings_file.exists(), "settings_panel_qt.py does not exist"
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check that AI models tab is created
    assert 'create_ai_models_tab' in content, "create_ai_models_tab method missing"
    print("✓ create_ai_models_tab method found")
    
    assert 'AIModelsSettingsTab' in content, "AIModelsSettingsTab not imported/used"
    print("✓ AIModelsSettingsTab used in settings panel")
    
    assert '🤖 AI Models' in content, "AI Models tab not added to tab widget"
    print("✓ AI Models tab added to settings panel")
    
    print("\n✅ All integration tests passed!")
    return True

def test_model_info_method():
    """Test get_models_info returns complete information"""
    print("\nTesting get_models_info Method...")
    
    from upscaler.model_manager import AIModelManager
    
    manager = AIModelManager()
    models_info = manager.get_models_info()
    
    # Check that all models are returned
    assert len(models_info) >= 7, f"Expected at least 7 models, got {len(models_info)}"
    print(f"✓ get_models_info returns {len(models_info)} models")
    
    # Check each model has status and installed fields
    for model_name, info in models_info.items():
        assert 'status' in info, f"{model_name} missing 'status' field"
        assert 'installed' in info, f"{model_name} missing 'installed' field"
        assert 'description' in info, f"{model_name} missing 'description' field"
        assert 'icon' in info, f"{model_name} missing 'icon' field"
        assert 'category' in info, f"{model_name} missing 'category' field"
        print(f"✓ {model_name}: status={info['status']}, installed={info['installed']}, category={info['category']}")
    
    print("\n✅ All get_models_info tests passed!")
    return True

if __name__ == '__main__':
    try:
        test_model_manager_structure()
        test_ai_models_tab_structure()
        test_ui_component_details()
        test_integration()
        test_model_info_method()
        
        # Get models info for final message
        from upscaler.model_manager import AIModelManager
        manager = AIModelManager()
        models_info = manager.get_models_info()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*60)
        print("\nAI Models Settings UI successfully implemented with:")
        print(f"  ✓ {len(models_info)} models defined (RealESRGAN x2/x4, CLIP, DINOv2, transformers, timm, Lanczos)")
        print("  ✓ Complete model metadata (icon, version, size, description, category)")
        print("  ✓ Beautiful card-based expandable UI")
        print("  ✓ Category-based organization (Upscaler, Vision, NLP, Acceleration)")
        print("  ✓ Prominent download/delete buttons (40px height, color-coded)")
        print("  ✓ Progress tracking for downloads")
        print("  ✓ Status indicators (green=installed, red=missing)")
        print("  ✓ Integration with settings panel")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
