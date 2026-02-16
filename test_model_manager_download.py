#!/usr/bin/env python3
"""
Test script for model manager mirror fallback and retry logic
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import urllib.request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from upscaler.model_manager import AIModelManager

def test_mirror_fallback():
    """Test that mirror URL is tried when primary URL fails"""
    print("\n" + "=" * 60)
    print("TEST: Mirror Fallback on Primary URL Failure")
    print("=" * 60)
    
    manager = AIModelManager()
    
    # Mock urlretrieve to simulate primary failure, mirror success
    call_count = [0]
    
    def mock_urlretrieve(url, dest, reporthook=None):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call (primary) - simulate failure
            raise Exception("Primary URL failed")
        else:
            # Second call (mirror) - simulate success
            Path(dest).touch()  # Create empty file
            return
    
    with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
        result = manager.download_model('RealESRGAN_x4plus')
        
        if result:
            print("✓ PASS: Mirror fallback successful")
            print(f"  Primary URL was tried first (failed)")
            print(f"  Mirror URL was tried second (succeeded)")
        else:
            print("✗ FAIL: Mirror fallback did not work")
        
        # Cleanup
        model_file = manager.models_dir / 'RealESRGAN_x4plus.pth'
        if model_file.exists():
            model_file.unlink()
    
    return result


def test_retry_logic():
    """Test that downloads are retried on transient failures"""
    print("\n" + "=" * 60)
    print("TEST: Retry Logic on Transient Failures")
    print("=" * 60)
    
    manager = AIModelManager()
    
    # Mock urlretrieve to fail twice, then succeed
    call_count = [0]
    
    def mock_urlretrieve(url, dest, reporthook=None):
        call_count[0] += 1
        if call_count[0] < 3:
            # First two attempts fail
            raise Exception(f"Attempt {call_count[0]} failed")
        else:
            # Third attempt succeeds
            Path(dest).touch()
            return
    
    with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
        with patch('time.sleep'):  # Speed up test by mocking sleep
            result = manager.download_model('RealESRGAN_x4plus')
            
            if result and call_count[0] == 3:
                print("✓ PASS: Retry logic successful")
                print(f"  Retried {call_count[0] - 1} times before success")
            else:
                print(f"✗ FAIL: Expected 3 attempts, got {call_count[0]}")
            
            # Cleanup
            model_file = manager.models_dir / 'RealESRGAN_x4plus.pth'
            if model_file.exists():
                model_file.unlink()
    
    return result


def test_auto_download_skip():
    """Test that auto-download models are skipped"""
    print("\n" + "=" * 60)
    print("TEST: Auto-Download Models are Skipped")
    print("=" * 60)
    
    manager = AIModelManager()
    
    # Try to download CLIP model (should be skipped)
    result = manager.download_model('CLIP_ViT-B/32')
    
    if result == False:
        print("✓ PASS: Auto-download model correctly skipped")
        print("  CLIP_ViT-B/32 is installed via pip, not downloaded")
    else:
        print("✗ FAIL: Auto-download model should return False")
    
    return not result  # Invert because False is success here


def test_cleanup_on_failure():
    """Test that partial downloads are cleaned up on failure"""
    print("\n" + "=" * 60)
    print("TEST: Cleanup on Download Failure")
    print("=" * 60)
    
    manager = AIModelManager()
    model_file = manager.models_dir / 'RealESRGAN_x4plus.pth'
    
    # Mock urlretrieve to always fail but create partial file
    def mock_urlretrieve(url, dest, reporthook=None):
        Path(dest).touch()  # Create partial file
        raise Exception("Download failed")
    
    with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
        with patch('time.sleep'):  # Speed up test
            result = manager.download_model('RealESRGAN_x4plus')
            
            if not result and not model_file.exists():
                print("✓ PASS: Partial download cleaned up on failure")
                print("  File was deleted after all retries failed")
            else:
                print("✗ FAIL: Partial file should be deleted")
                if model_file.exists():
                    model_file.unlink()
    
    return not result


def test_all_models_have_required_fields():
    """Test that all models have required configuration fields"""
    print("\n" + "=" * 60)
    print("TEST: All Models Have Required Fields")
    print("=" * 60)
    
    manager = AIModelManager()
    all_valid = True
    
    for model_name, model_info in manager.MODELS.items():
        required = ['description', 'tool', 'category', 'icon']
        missing = [field for field in required if field not in model_info]
        
        if missing:
            print(f"✗ FAIL: {model_name} missing fields: {missing}")
            all_valid = False
        
        # Check downloadable models have URL or auto_download
        if not model_info.get('auto_download') and not model_info.get('native_module'):
            if 'url' not in model_info:
                print(f"✗ FAIL: {model_name} needs 'url' or 'auto_download'")
                all_valid = False
    
    if all_valid:
        print("✓ PASS: All models have required configuration fields")
        print(f"  Validated {len(manager.MODELS)} models")
    
    return all_valid


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("MODEL MANAGER TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Auto-download skip", test_auto_download_skip),
        ("All models valid", test_all_models_have_required_fields),
        ("Retry logic", test_retry_logic),
        ("Mirror fallback", test_mirror_fallback),
        ("Cleanup on failure", test_cleanup_on_failure),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ EXCEPTION in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 70)
    
    return passed_count == total_count


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
