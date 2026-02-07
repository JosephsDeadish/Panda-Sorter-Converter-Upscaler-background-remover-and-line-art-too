#!/usr/bin/env python3
"""
Panda Mode Feature Demo
Demonstrates the enhanced Panda Mode features for PS2 Texture Sorter
"""

import sys
import time
sys.path.insert(0, 'src/features')
from panda_mode import PandaMode, PandaMood


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_tooltips():
    """Demo the tooltip system."""
    print_section("1. RANDOMIZED TOOLTIP SYSTEM")
    
    panda_normal = PandaMode(vulgar_mode=False)
    panda_vulgar = PandaMode(vulgar_mode=True)
    
    actions = ['sort_button', 'convert_button', 'undo_button']
    
    for action in actions:
        print(f"\n{action.replace('_', ' ').title()}:")
        print(f"  Normal:  {panda_normal.get_tooltip(action)}")
        print(f"  Vulgar:  {panda_vulgar.get_tooltip(action)}")


def demo_moods():
    """Demo mood system."""
    print_section("2. PANDA MOOD SYSTEM")
    
    panda = PandaMode(vulgar_mode=True)
    
    moods_to_test = [
        (PandaMood.HAPPY, "Starting happy"),
        (PandaMood.WORKING, "Getting to work"),
        (PandaMood.SARCASTIC, "User being slow..."),
        (PandaMood.RAGE, "After 5 failures!"),
        (PandaMood.CELEBRATING, "Success!"),
        (PandaMood.EXISTENTIAL, "After 10,000 files..."),
    ]
    
    for mood, description in moods_to_test:
        panda.set_mood(mood)
        indicator = panda.get_panda_mood_indicator()
        print(f"  {indicator} {mood.value:15s} - {description}")


def demo_easter_eggs():
    """Demo easter egg system."""
    print_section("3. EASTER EGG TRIGGERS")
    
    panda = PandaMode(vulgar_mode=True)
    
    print("\nTriggering some easter eggs...")
    
    # Click spam
    print("\n  • Clicking panda 10 times...")
    for i in range(10):
        response = panda.on_panda_click()
    print(f"    Result: {response}")
    
    # Text-based
    print("\n  • Typing 'bamboo'...")
    panda.handle_text_input('bamboo')
    print(f"    Easter eggs: {list(panda.easter_eggs_triggered)}")
    
    # Zero byte file
    print("\n  • Processing 0 byte file...")
    panda2 = PandaMode(vulgar_mode=True)
    panda2.track_file_processed('/test/empty.png', 0)
    print(f"    Easter eggs: {list(panda2.easter_eggs_triggered)}")
    
    # Same file twice
    print("\n  • Processing same file twice...")
    panda3 = PandaMode(vulgar_mode=False)
    panda3.track_file_processed('/test/texture.png', 1024)
    panda3.track_file_processed('/test/texture.png', 1024)
    print(f"    Easter eggs: {list(panda3.easter_eggs_triggered)}")


def demo_interactive():
    """Demo interactive features."""
    print_section("4. INTERACTIVE PANDA PET")
    
    panda = PandaMode(vulgar_mode=False)
    
    print("\n  Panda Click:")
    for i in range(3):
        response = panda.on_panda_click()
        print(f"    Click {i+1}: {response}")
    
    print("\n  Panda Hover:")
    for i in range(3):
        thought = panda.on_panda_hover()
        print(f"    Thought {i+1}: {thought}")
    
    print("\n  Right-Click Menu:")
    menu = panda.on_panda_right_click()
    for key, value in menu.items():
        print(f"    {value}")
    
    print("\n  Petting the Panda:")
    for i in range(3):
        reaction = panda.pet_panda_minigame()
        print(f"    Pet {i+1}: {reaction}")


def demo_tracking():
    """Demo tracking features."""
    print_section("5. TRACKING & AUTOMATION")
    
    panda = PandaMode(vulgar_mode=True)
    
    print("\n  Tracking operations...")
    panda.track_file_processed('/test/file1.png', 2048)
    panda.track_file_processed('/test/file2.png', 4096)
    panda.track_operation_cancel()
    panda.track_operation_failure()
    panda.on_panda_click()
    panda.on_panda_click()
    
    stats = panda.get_statistics()
    print(f"\n  Statistics:")
    print(f"    Files processed: {stats['files_processed']}")
    print(f"    Click count: {stats['click_count']}")
    print(f"    Failed operations: {stats['failed_operations']}")
    print(f"    Cancellations: {stats['operation_cancellations']}")
    print(f"    Easter eggs found: {stats['easter_eggs_triggered']}")


def demo_special_modes():
    """Demo special behavior modes."""
    print_section("6. SPECIAL BEHAVIOR MODES")
    
    panda = PandaMode(vulgar_mode=True)
    
    print("\n  Tech Support Mode:")
    quote = panda.get_random_tech_support_quote()
    print(f"    {quote}")
    
    print("\n  Motivational Mode:")
    quote = panda.motivate_user()
    print(f"    {quote}")
    
    print("\n  Sarcastic Mode:")
    response = panda.become_sarcastic()
    print(f"    {response}")
    
    print("\n  Triggering Rage Mode (5 failures)...")
    panda2 = PandaMode(vulgar_mode=True)
    for i in range(5):
        panda2.track_operation_failure()
    print(f"    Current mood: {panda2.current_mood.value} {panda2.get_panda_mood_indicator()}")


def demo_animations():
    """Demo ASCII art animations."""
    print_section("7. ASCII ART ANIMATIONS")
    
    panda = PandaMode(vulgar_mode=False)
    
    animations = ['idle', 'working', 'celebrating', 'rage', 'drunk', 'sarcastic']
    
    for anim in animations:
        print(f"\n  {anim.upper()} Animation:")
        frame = panda.get_animation_frame(anim)
        print(frame)


def main():
    """Run the demo."""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     🐼 PANDA MODE ENHANCED FEATURES DEMONSTRATION 🐼      ║")
    print("║           PS2 Texture Sorter - Panda Edition              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    try:
        demo_tooltips()
        demo_moods()
        demo_easter_eggs()
        demo_interactive()
        demo_tracking()
        demo_special_modes()
        demo_animations()
        
        print_section("DEMO COMPLETE!")
        print("\n✅ All enhanced features demonstrated successfully!")
        print("\nFeature Summary:")
        print(f"  • {len(PandaMode.TOOLTIPS)} tooltip actions (6 variants each)")
        print(f"  • {len(PandaMood)} mood states with unique behaviors")
        print(f"  • {len(PandaMode.EASTER_EGGS)} easter egg triggers")
        print(f"  • Interactive panda pet with click/hover/pet mechanics")
        print(f"  • Comprehensive tracking for smart behavior triggers")
        print(f"  • 9 ASCII art animation frames")
        print("\n🎋 Panda Mode: Making texture sorting fun since 2024! 🎋\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
