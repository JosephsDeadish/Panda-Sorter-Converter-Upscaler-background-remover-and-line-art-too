"""
Test script for Game Identifier functionality
Tests serial detection, CRC detection, and game identification
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.game_identifier import GameIdentifier, GameInfo

def test_serial_detection():
    """Test serial detection from various path formats"""
    print("\n=== Testing Serial Detection ===")
    
    identifier = GameIdentifier()
    
    test_cases = [
        (Path("/textures/SLUS-20917"), "SLUS-20917", "NTSC-U"),
        (Path("/games/SLUS_20946/textures"), "SLUS-20946", "NTSC-U"),
        (Path("C:/PCSX2/SCUS-12345"), "SCUS-12345", "NTSC-U"),
        (Path("/pal/SLES-12345/dump"), "SLES-12345", "PAL"),
        (Path("/japan/SLPS-12345"), "SLPS-12345", "NTSC-J"),
    ]
    
    for path, expected_serial, expected_region in test_cases:
        result = identifier.detect_serial_from_path(path)
        if result:
            serial, region = result
            status = "✓" if serial == expected_serial and region == expected_region else "✗"
            print(f"{status} Path: {path}")
            print(f"  Expected: {expected_serial} ({expected_region})")
            print(f"  Got: {serial} ({region})")
        else:
            print(f"✗ Path: {path} - No serial detected")

def test_crc_detection():
    """Test CRC detection from folder names"""
    print("\n=== Testing CRC Detection ===")
    
    identifier = GameIdentifier()
    
    test_cases = [
        (Path("/textures/12AB34CD/dump"), "12AB34CD"),
        (Path("/games/God_of_War_ABCD1234"), "ABCD1234"),
        (Path("C:/PCSX2/textures/SLUS-20917-DEADBEEF"), "DEADBEEF"),
    ]
    
    for path, expected_crc in test_cases:
        result = identifier.detect_crc_from_path(path)
        status = "✓" if result == expected_crc.upper() else "✗"
        print(f"{status} Path: {path}")
        print(f"  Expected: {expected_crc.upper()}")
        print(f"  Got: {result}")

def test_game_lookup():
    """Test game lookup by serial"""
    print("\n=== Testing Game Lookup ===")
    
    identifier = GameIdentifier()
    
    # Test with known games
    test_serials = ["SLUS-20917", "SLUS-20778", "SLUS-20584"]
    
    for serial in test_serials:
        game_info = identifier.lookup_by_serial(serial)
        if game_info:
            print(f"✓ Serial: {serial}")
            print(f"  Title: {game_info.title}")
            print(f"  Region: {game_info.region}")
            print(f"  Confidence: {game_info.confidence:.0%}")
            if game_info.texture_profile:
                print(f"  Has texture profile: Yes")
        else:
            print(f"✗ Serial: {serial} - Not found")

def test_identify_game():
    """Test full game identification from path"""
    print("\n=== Testing Full Game Identification ===")
    
    identifier = GameIdentifier()
    
    # Test with paths containing known game serials
    test_paths = [
        Path("/textures/SLUS-20917/dump"),
        Path("/games/GodOfWar/SLUS-20778"),
        Path("/unknown/random_folder"),
    ]
    
    for path in test_paths:
        game_info = identifier.identify_game(path, scan_files=False)
        if game_info:
            print(f"✓ Path: {path}")
            print(f"  Game: {game_info.title}")
            print(f"  Serial: {game_info.serial}")
            print(f"  Confidence: {game_info.confidence:.0%}")
            print(f"  Source: {game_info.source}")
        else:
            print(f"✗ Path: {path} - No game identified")

def test_add_custom_game():
    """Test adding a custom game to the database"""
    print("\n=== Testing Custom Game Addition ===")
    
    identifier = GameIdentifier()
    
    # Add a custom game
    success = identifier.add_known_game(
        serial="SLUS-99999",
        title="Test Game",
        region="NTSC-U",
        texture_profile={
            'common_categories': ['test', 'demo'],
            'icon_shapes': 'square'
        }
    )
    
    if success:
        print("✓ Custom game added successfully")
        
        # Try to look it up
        game_info = identifier.lookup_by_serial("SLUS-99999")
        if game_info:
            print(f"  Title: {game_info.title}")
            print(f"  Profile: {game_info.texture_profile}")
        else:
            print("✗ Failed to lookup added game")
    else:
        print("✗ Failed to add custom game")

def test_texture_profile():
    """Test getting texture profile for a game"""
    print("\n=== Testing Texture Profile Retrieval ===")
    
    identifier = GameIdentifier()
    
    # Get game info
    game_info = identifier.lookup_by_serial("SLUS-20917")
    if game_info:
        profile = identifier.get_texture_profile(game_info)
        print(f"✓ Game: {game_info.title}")
        print(f"  Common Categories: {profile.get('common_categories', [])}")
        print(f"  Icon Shapes: {profile.get('icon_shapes', 'N/A')}")
        print(f"  Atlas Layout: {profile.get('atlas_layout', 'N/A')}")
    else:
        print("✗ Game not found")

if __name__ == "__main__":
    print("=" * 60)
    print("Game Identifier Test Suite")
    print("=" * 60)
    
    try:
        test_serial_detection()
        test_crc_detection()
        test_game_lookup()
        test_identify_game()
        test_add_custom_game()
        test_texture_profile()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
