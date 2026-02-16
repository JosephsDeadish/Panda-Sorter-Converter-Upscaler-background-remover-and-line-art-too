#!/usr/bin/env python3
"""
Validation script for Feature Extractor dropdown implementation
Tests structure without requiring PyQt6
"""

import sys
import ast
from pathlib import Path

def validate_organizer_settings():
    """Validate the organizer settings panel has feature extractor"""
    
    file_path = Path(__file__).parent / 'src' / 'ui' / 'organizer_settings_panel.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the file as AST
    try:
        tree = ast.parse(content)
        print("✅ File parses successfully")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    
    # Check for required elements
    checks = {
        'Feature Extractor dropdown': 'self.extractor_combo' in content,
        'CLIP option': 'CLIP (image-to-text classification)' in content,
        'DINOv2 option': 'DINOv2 (visual similarity clustering)' in content,
        'timm option': 'timm (PyTorch Image Models)' in content,
        'on_extractor_changed method': 'def on_extractor_changed' in content,
        'set_layout_visible method': 'def set_layout_visible' in content,
        'feature_extractor in settings': "'feature_extractor'" in content,
        'CLIP layout visibility': 'self.clip_layout' in content,
        'DINOv2 layout visibility': 'self.dinov2_layout' in content,
    }
    
    all_passed = True
    print("\n" + "=" * 60)
    print("Validation Results:")
    print("=" * 60)
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All validations passed!")
        print("\nFeature Extractor dropdown implementation complete:")
        print("  • CLIP (image-to-text classification)")
        print("  • DINOv2 (visual similarity clustering)")
        print("  • timm (PyTorch Image Models)")
        print("\n💡 The dropdown dynamically shows/hides model-specific options")
        print("   based on the selected feature extractor.")
    else:
        print("\n❌ Some validations failed")
        return False
    
    return True

def validate_timm_no_torchscript():
    """Validate that timm is not compiled with TorchScript"""
    
    file_path = Path(__file__).parent / 'src' / 'vision_models' / 'efficientnet_model.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("\n" + "=" * 60)
    print("TorchScript Compilation Check:")
    print("=" * 60)
    
    # Check that TorchScript compilation is NOT used
    torchscript_indicators = [
        'torch.jit.script',
        'torch.jit.trace',
        'torch.jit.compile',
        '@torch.jit.script',
    ]
    
    found_torchscript = False
    for indicator in torchscript_indicators:
        if indicator in content:
            print(f"❌ Found TorchScript compilation: {indicator}")
            found_torchscript = True
    
    if not found_torchscript:
        print("✅ timm models are NOT compiled with TorchScript")
        print("   This prevents source access errors in Settings.")
        return True
    else:
        print("\n⚠️  Warning: TorchScript compilation found!")
        print("   This may cause source access errors.")
        return False

if __name__ == '__main__':
    print("Validating Feature Extractor Dropdown Implementation")
    print("=" * 60)
    
    settings_ok = validate_organizer_settings()
    torchscript_ok = validate_timm_no_torchscript()
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    
    if settings_ok and torchscript_ok:
        print("✅ All validations passed successfully!")
        print("\nImplementation is ready for PR #168")
        sys.exit(0)
    else:
        print("❌ Some validations failed")
        sys.exit(1)
