#!/usr/bin/env python3
"""
Test LOD detector fix
Validates that detect_lods() method exists and works with Path objects
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.lod_detector.lod_detector import LODDetector


def test_detect_lods_exists():
    """Test that detect_lods method exists"""
    detector = LODDetector()
    assert hasattr(detector, 'detect_lods'), "detect_lods method should exist"
    print("✓ detect_lods method exists")


def test_detect_lods_with_path_objects():
    """Test that detect_lods works with Path objects"""
    detector = LODDetector()
    
    # Create test paths
    test_paths = [
        Path("/test/texture_lod0.dds"),
        Path("/test/texture_lod1.dds"),
        Path("/test/other_texture.png"),
    ]
    
    # Call detect_lods
    result = detector.detect_lods(test_paths)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert len(result) > 0, "Should return grouped results"
    print(f"✓ detect_lods works with Path objects, found {len(result)} groups")


def test_group_lods_compatibility():
    """Test that group_lods also works"""
    detector = LODDetector()
    
    test_paths = [
        Path("/test/model_lod0.dds"),
        Path("/test/model_lod1.dds"),
    ]
    
    result = detector.group_lods(test_paths)
    assert isinstance(result, dict), "group_lods should return dictionary"
    print("✓ group_lods works correctly")


def test_detect_lods_is_alias():
    """Test that detect_lods returns same structure as group_lods"""
    detector = LODDetector()
    
    test_paths = [Path("/test/tex_lod0.dds")]
    
    result1 = detector.detect_lods(test_paths)
    result2 = detector.group_lods(test_paths)
    
    # Both should return dict with same structure
    assert type(result1) == type(result2), "Both methods should return same type"
    print("✓ detect_lods and group_lods return compatible structures")


if __name__ == "__main__":
    print("Testing LOD Detector Fix...")
    print("-" * 50)
    
    try:
        test_detect_lods_exists()
        test_detect_lods_with_path_objects()
        test_group_lods_compatibility()
        test_detect_lods_is_alias()
        
        print("-" * 50)
        print("✅ All LOD detector tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
