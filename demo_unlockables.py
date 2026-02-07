#!/usr/bin/env python3
"""
Demo script for Unlockables System and Enhanced Panda Mode
Shows off all the new features: cursors, outfits, themes, animations, feeding, and travel
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from features.unlockables_system import UnlockablesSystem
from features.panda_mode import PandaFeedingSystem, PandaTravelSystem


def print_header(text: str):
    """Print a fancy header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def demo_unlockables():
    """Demonstrate the unlockables system."""
    print_header("🎮 UNLOCKABLES SYSTEM DEMO")
    
    # Create system
    unlockables = UnlockablesSystem()
    
    # Show initial state
    print("📊 Initial State:")
    summary = unlockables.get_summary()
    print(f"  Total Cursors: {summary['total_counts']['cursors']}")
    print(f"  Total Outfits: {summary['total_counts']['outfits']}")
    print(f"  Total Themes: {summary['total_counts']['themes']}")
    print(f"  Total Animations: {summary['total_counts']['animations']}")
    print(f"  Total Tooltip Collections: {summary['total_counts']['tooltip_collections']}")
    print(f"  Completion: {summary['completion_percentage']['overall']:.1f}%")
    
    # Show unlocked cursors
    print("\n🖱️  Unlocked Cursors:")
    for cursor in unlockables.get_unlocked_cursors():
        print(f"  🖱️  {cursor.name}")
    
    # Show unlocked outfits
    print("\n👔 Unlocked Outfits:")
    for outfit in unlockables.get_unlocked_outfits():
        print(f"  👔 {outfit.name}")
    
    # Simulate progress
    print_header("📈 SIMULATING PROGRESS")
    
    print("Processing 1000 files...")
    unlockables.update_stat('total_files_processed', 1000)
    
    print("Feeding panda 10 times...")
    unlockables.update_stat('panda_feed_count', 10)
    
    print("Petting panda 100 times...")
    unlockables.update_stat('panda_pet_count', 100)
    
    print("Using for 1 hour...")
    unlockables.update_stat('session_time_minutes', 60)
    
    # Show updated state
    print("\n📊 Updated State:")
    summary = unlockables.get_summary()
    print(f"  Unlocked Cursors: {summary['unlocked_counts']['cursors']}/{summary['total_counts']['cursors']}")
    print(f"  Unlocked Outfits: {summary['unlocked_counts']['outfits']}/{summary['total_counts']['outfits']}")
    print(f"  Unlocked Themes: {summary['unlocked_counts']['themes']}/{summary['total_counts']['themes']}")
    print(f"  Completion: {summary['completion_percentage']['overall']:.1f}%")
    
    # Show newly unlocked items
    print("\n🎉 Newly Unlocked Items:")
    for cursor in unlockables.get_unlocked_cursors():
        if cursor.id not in ['default', 'skull', 'panda', 'sword', 'arrow']:
            print(f"  🖱️  {cursor.name} - {cursor.description}")
    
    for outfit in unlockables.get_unlocked_outfits():
        if outfit.id != 'default':
            print(f"  👔 {outfit.name} - {outfit.description}")
    
    for theme in unlockables.get_unlocked_themes():
        print(f"  🎨 {theme.name} - {theme.description}")
    
    # Show random tooltips
    print("\n💬 Random Tooltips from Unlocked Collections:")
    for _ in range(3):
        tooltip = unlockables.get_random_tooltip()
        if tooltip:
            print(f"  • {tooltip}")


def demo_feeding():
    """Demonstrate the feeding system."""
    print_header("🍜 PANDA FEEDING SYSTEM DEMO")
    
    feeding = PandaFeedingSystem()
    stats = {'files_processed': 500, 'elapsed_time_hours': 1, 'panda_pet_count': 50}
    
    # Show hunger
    print(feeding.get_hunger_level())
    
    # Show available foods
    available = feeding.get_available_foods(stats)
    print(f"\n🍴 Available Foods ({len(available)}):")
    for food_id in available[:5]:
        food = feeding.FOOD_ITEMS[food_id]
        print(f"  {food.icon} {food.name} - {food.description} (+{food.happiness_bonus} happiness)")
    
    # Feed panda multiple times
    print("\n🐼 Feeding Panda:")
    foods_to_try = ['bamboo', 'cookies', 'ramen', 'pizza']
    for food_id in foods_to_try:
        if food_id in available:
            result = feeding.feed_panda(food_id, stats)
            print(f"\n{result}")
            print(f"  Feed Count: {feeding.feed_count}")
            print(f"  Hunger: {feeding.hunger_level:.1f}/100")
    
    # Show hunger after feeding
    print("\n" + feeding.get_hunger_level())


def demo_travel():
    """Demonstrate the travel system."""
    print_header("✈️  PANDA TRAVEL SYSTEM DEMO")
    
    travel = PandaTravelSystem()
    stats = {
        'files_processed': 1000,
        'elapsed_time_hours': 2,
        'panda_pet_count': 25,
        'days_used': 5
    }
    
    # Show current location
    print(travel.get_panda_location())
    
    # Show available locations
    available = travel.get_available_locations(stats)
    print(f"\n🗺️  Available Locations ({len(available)}):")
    for loc_id in available[:8]:
        location = travel.LOCATIONS[loc_id]
        print(f"  {location.icon} {location.name} - {location.description}")
    
    # Travel to some locations
    print("\n🐼 Panda Adventures:")
    destinations = ['bamboo_forest', 'beach', 'library', 'cafe']
    
    for dest in destinations:
        if dest in available:
            print(f"\n{travel.send_panda_to(dest, stats)}")
            print(f"{travel.get_panda_postcard()}")
    
    # Show travel stats
    print(f"\n📊 Travel Stats:")
    print(f"  Locations Visited: {len(travel.visited_locations)}/{len(travel.LOCATIONS)}")
    print(f"  Total Trips: {travel.travel_count}")
    print(f"  Current Location: {travel.current_location}")


def demo_integration():
    """Demonstrate integration between systems."""
    print_header("🔗 INTEGRATION DEMO")
    
    print("Creating all systems...")
    unlockables = UnlockablesSystem()
    feeding = PandaFeedingSystem()
    travel = PandaTravelSystem()
    
    # Simulate a play session
    print("\n🎮 Simulating a Play Session:")
    
    print("\n1. Processing 500 files...")
    unlockables.update_stat('total_files_processed', 500)
    
    print("2. Feeding panda bamboo...")
    stats = {'files_processed': 500, 'elapsed_time_hours': 0.5}
    result = feeding.feed_panda('bamboo', stats)
    print(f"   {result}")
    
    print("\n3. Sending panda to library...")
    travel_stats = {'files_processed': 500, 'elapsed_time_hours': 0.5}
    result = travel.send_panda_to('library', travel_stats)
    print(f"   {result}")
    
    print("\n4. Processing more files...")
    unlockables.update_stat('total_files_processed', 500)
    
    print("\n5. Getting postcard from panda...")
    print(f"   {travel.get_panda_postcard()}")
    
    # Show final summary
    print("\n📊 Session Summary:")
    summary = unlockables.get_summary()
    print(f"  Files Processed: {summary['stats']['total_files_processed']}")
    print(f"  Feed Count: {feeding.feed_count}")
    print(f"  Locations Visited: {len(travel.visited_locations)}")
    print(f"  New Unlocks: {summary['unlocked_counts']['cursors'] + summary['unlocked_counts']['outfits'] + summary['unlocked_counts']['themes']}")


def show_ascii_art():
    """Show some fun ASCII art."""
    print("\n")
    print("        🎮 PS2 TEXTURE SORTER 🎮")
    print("    ／人◕ ‿‿ ◕人＼")
    print("   ╱人◕ ‿‿ ◕人╲")
    print("  <人◕  ‿‿  ◕人>")
    print("   ＼(◕  ‿‿  ◕)／")
    print("\n    Unlockables & Panda Mode Demo")
    print()


def main():
    """Run all demos."""
    show_ascii_art()
    
    try:
        # Run demos
        demo_unlockables()
        demo_feeding()
        demo_travel()
        demo_integration()
        
        # Final message
        print_header("✅ DEMO COMPLETE")
        print("All systems working perfectly! 🎉")
        print("\nFeatures Demonstrated:")
        print("  ✓ 70+ Unlockable items")
        print("  ✓ Panda feeding with 14 foods")
        print("  ✓ Panda travel with 16 locations")
        print("  ✓ Progress tracking and statistics")
        print("  ✓ Integration between systems")
        print("\n🐼 Happy sorting! 🎋\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
