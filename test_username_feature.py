"""
Test Username Personalization Feature
Tests the username feature added to the panda character
"""

import sys
import os
import random

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.features.panda_character import PandaCharacter, PandaGender
from src.config import config

def test_username_initialization():
    """Test that PandaCharacter can be initialized with username."""
    print("Testing username initialization...")
    
    # Test default initialization (no username)
    panda1 = PandaCharacter()
    assert panda1.username == "", "Default username should be empty string"
    
    # Test with username
    panda2 = PandaCharacter(username="TestUser")
    assert panda2.username == "TestUser", "Username should be set correctly"
    
    # Test with all parameters
    panda3 = PandaCharacter(name="Bamboo", gender=PandaGender.FEMALE, username="Alice")
    assert panda3.name == "Bamboo", "Name should be set correctly"
    assert panda3.gender == PandaGender.FEMALE, "Gender should be set correctly"
    assert panda3.username == "Alice", "Username should be set correctly"
    
    print("✓ Username initialization works correctly")

def test_set_username():
    """Test the set_username method."""
    print("Testing set_username method...")
    
    panda = PandaCharacter()
    assert panda.username == "", "Initial username should be empty"
    
    panda.set_username("Bob")
    assert panda.username == "Bob", "Username should be updated"
    
    panda.set_username("Charlie")
    assert panda.username == "Charlie", "Username should be updated again"
    
    print("✓ set_username method works correctly")

def test_personalize_message():
    """Test the _personalize_message helper method."""
    print("Testing _personalize_message method...")
    
    # Test without username
    panda1 = PandaCharacter()
    msg = panda1._personalize_message("Hello!")
    assert msg == "Hello!", "Message should not be personalized without username"
    
    # Test with username - use fixed seed for predictable results
    random.seed(42)
    panda2 = PandaCharacter(username="David")
    
    # Test multiple times to see both personalized and non-personalized
    personalized_count = 0
    original_count = 0
    for _ in range(20):
        msg = panda2._personalize_message("Ready to work!")
        if "David" in msg:
            personalized_count += 1
        else:
            original_count += 1
    
    assert personalized_count > 0, "Some messages should be personalized"
    assert original_count > 0, "Some messages should remain unpersonalized"
    
    print(f"✓ _personalize_message works correctly (personalized: {personalized_count}, original: {original_count})")

def test_click_with_username():
    """Test that on_click responses can include username."""
    print("Testing on_click with username...")
    
    random.seed(123)
    panda = PandaCharacter(username="Eve")
    
    # Get several click responses
    personalized_count = 0
    for _ in range(20):
        response = panda.on_click()
        if "Eve" in response:
            personalized_count += 1
    
    assert personalized_count > 0, "At least some click responses should include username"
    
    print(f"✓ on_click with username works correctly (personalized: {personalized_count}/20)")

def test_config_username_field():
    """Test that username field exists in config."""
    print("Testing config username field...")
    
    # Check that username field exists in config defaults
    username = config.get('panda', 'username', default=None)
    assert username is not None, "Username field should exist in config"
    
    print("✓ Config username field exists")

def test_new_dialogues():
    """Test that new converter-related dialogues exist and are reachable."""
    print("Testing new converter-related dialogues...")
    
    converter_messages = [
        "🐼 I see you looking at the converter!",
        "🐼 The converter can do many formats!",
        "🐼 Looking forward to seeing you again!",
    ]
    
    # Check messages exist in CLICK_RESPONSES
    for msg in converter_messages:
        assert msg in PandaCharacter.CLICK_RESPONSES, f"Missing dialogue: {msg}"
    
    # Verify these messages are actually reachable through on_click()
    random.seed(999)
    panda = PandaCharacter()
    responses_seen = set()
    
    # Call on_click many times to collect unique responses
    for _ in range(200):
        response = panda.on_click()
        responses_seen.add(response)
    
    # Check if at least one of the new messages was returned
    found_new_messages = [msg for msg in converter_messages if msg in responses_seen]
    assert len(found_new_messages) > 0, f"New dialogues should be reachable via on_click(). Seen: {len(responses_seen)} unique messages"
    
    print(f"✓ New converter-related dialogues added and reachable (found {len(found_new_messages)}/3 in {len(responses_seen)} unique responses)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Username Personalization Feature")
    print("="*60 + "\n")
    
    try:
        test_username_initialization()
        test_set_username()
        test_personalize_message()
        test_click_with_username()
        test_config_username_field()
        test_new_dialogues()
        
        print("\n" + "="*60)
        print("✓ All username feature tests passed!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
