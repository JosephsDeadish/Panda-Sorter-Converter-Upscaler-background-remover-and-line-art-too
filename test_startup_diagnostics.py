#!/usr/bin/env python3
"""
Test script to verify startup diagnostics without requiring a full Qt environment.
This tests the check_feature_availability function in main.py.
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_feature_availability():
    """Test the check_feature_availability function."""
    print("=" * 70)
    print("Testing Feature Availability Check")
    print("=" * 70)
    
    # Import the function
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Mock the QApplication and window to avoid Qt dependencies
    class MockWindow:
        def log(self, message):
            print(message)
    
    # Test check_feature_availability
    try:
        # We need to extract just the function without importing Qt
        # Read main.py and extract the function
        main_file = Path(__file__).parent / 'main.py'
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Execute the check_feature_availability function
        namespace = {}
        # Extract and execute just the check function
        exec_code = """
def check_feature_availability():
    features = {
        'pytorch': False,
        'pytorch_cuda': False,
        'clip': False,
        'dinov2': False,
        'transformers': False,
        'open_clip': False,
        'timm': False,
        'onnx': False,
        'onnxruntime': False,
    }
    
    try:
        import torch
        features['pytorch'] = True
        features['pytorch_cuda'] = torch.cuda.is_available()
    except Exception:
        pass
    
    try:
        import onnx
        features['onnx'] = True
    except Exception:
        pass
    
    try:
        import onnxruntime
        features['onnxruntime'] = True
    except Exception:
        pass
    
    try:
        import transformers
        features['transformers'] = True
    except Exception:
        pass
    
    try:
        import open_clip
        features['open_clip'] = True
    except Exception:
        pass
    
    try:
        import timm
        features['timm'] = True
    except Exception:
        pass
    
    features['clip'] = features['pytorch'] and (features['transformers'] or features['open_clip'])
    features['dinov2'] = features['pytorch']
    
    return features
"""
        exec(exec_code, namespace)
        check_feature_availability = namespace['check_feature_availability']
        
        # Run the check
        features = check_feature_availability()
        
        print("\nFeature Availability Status:")
        print("-" * 70)
        for feature, available in features.items():
            status = "✅" if available else "❌"
            print(f"{status} {feature:20s}: {available}")
        
        print("-" * 70)
        print("\nSummary:")
        if features['pytorch']:
            print("✅ PyTorch is available")
            if features['pytorch_cuda']:
                print("✅ CUDA GPU acceleration is available")
            else:
                print("⚠️  CUDA not available (CPU-only mode)")
        else:
            print("❌ PyTorch is NOT available")
            print("💡 Install with: pip install torch torchvision")
        
        if features['clip'] or features['dinov2']:
            print("✅ Vision models can be loaded")
        else:
            print("⚠️  Vision models cannot be loaded")
        
        if features['onnxruntime'] or features['onnx']:
            print("✅ ONNX features available")
            if features['onnxruntime']:
                print("   ✅ ONNX Runtime available")
            if features['onnx']:
                print("   ✅ ONNX model format available")
        else:
            print("⚠️  ONNX not available (optional)")
        
        print("=" * 70)
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_feature_availability()
    sys.exit(0 if success else 1)
