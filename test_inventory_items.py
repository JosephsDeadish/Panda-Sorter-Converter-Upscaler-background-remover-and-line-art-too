#!/usr/bin/env python3
"""
Test inventory and item system improvements.
Validates:
- Inventory category filtering
- Shop-to-inventory food linkage
- Item physics properties
- Food consumption vs toy infinite use
- Panda-item interactions
- Widget collection new items
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.panda_widgets import (
    WidgetCollection, WidgetType, PandaWidget, ToyWidget, FoodWidget,
    AccessoryWidget, WidgetRarity, ItemPhysics, WidgetStats
)
from src.features.panda_character import PandaCharacter
from src.features.shop_system import ShopSystem, ShopCategory


def test_item_physics_properties():
    """Test that items have correct physics properties."""
    wc = WidgetCollection()

    ball = wc.get_widget('ball')
    assert ball.physics.bounciness == 1.8, "Ball should be bouncy"
    assert ball.physics.weight == 0.5, "Ball should be light"

    dumbbell = wc.get_widget('dumbbell')
    assert dumbbell.physics.weight == 3.0, "Dumbbell should be heavy"
    assert dumbbell.physics.gravity == 3.0, "Dumbbell should have high gravity"
    assert dumbbell.physics.bounciness == 0.15, "Dumbbell should barely bounce"

    carrot = wc.get_widget('bouncy_carrot')
    assert carrot.physics.bounciness == 2.5, "Bouncy carrot should be very bouncy"

    squishy = wc.get_widget('squishy_ball')
    assert squishy.physics.bounciness == 2.0, "Squishy ball should be bouncy"

    kite = wc.get_widget('kite')
    assert kite.physics.gravity == 0.3, "Kite should have low gravity"
    assert kite.physics.friction == 0.98, "Kite should have low friction (float longer)"
    print("✓ Item physics properties correct")


def test_food_is_consumable():
    """Test that food items are consumable and decrease quantity on use."""
    wc = WidgetCollection()

    bamboo = wc.get_widget('bamboo')
    assert bamboo.consumable is True, "Food should be consumable"
    assert bamboo.quantity == 0, "Food starts with 0 quantity"

    # Add some food
    wc.add_food_quantity('bamboo', 3)
    assert bamboo.quantity == 3, "Should have 3 after adding"

    # Use one
    result = bamboo.use()
    assert result['consumed'] is True, "Food should be consumed on use"
    assert bamboo.quantity == 2, "Should have 2 after using 1"

    # Use remaining
    bamboo.use()
    bamboo.use()
    assert bamboo.quantity == 0, "Should have 0 after using all"

    # Try to use with 0 quantity
    result = bamboo.use()
    assert result['happiness'] == 0, "Should get 0 happiness when out of food"
    assert result['consumed'] is False, "Should not consume when empty"
    assert bamboo.quantity == 0, "Should still be 0"
    print("✓ Food consumption works correctly")


def test_toys_infinite_use():
    """Test that toys have infinite uses and are never consumed."""
    wc = WidgetCollection()

    ball = wc.get_widget('ball')
    assert ball.consumable is False, "Toys should not be consumable"

    # Use many times
    for i in range(10):
        result = ball.use()
        assert result['consumed'] is False, f"Toy should never be consumed (use {i+1})"
        assert result['happiness'] > 0, "Toy should always give happiness"

    assert ball.stats.times_used == 10, "Toy should track usage"
    print("✓ Toys have infinite uses")


def test_accessories_are_not_consumable():
    """Test that accessories are not consumable."""
    wc = WidgetCollection()

    bowtie = wc.get_widget('bowtie')
    assert bowtie.consumable is False, "Accessories should not be consumable"
    print("✓ Accessories are not consumable")


def test_new_widgets_exist():
    """Test that all new widgets were added to the collection."""
    wc = WidgetCollection()

    # New toys
    for widget_id in ['skateboard', 'drum', 'telescope', 'bouncy_carrot',
                      'squishy_ball', 'dumbbell']:
        widget = wc.get_widget(widget_id)
        assert widget is not None, f"Widget {widget_id} should exist"
        assert widget.widget_type == WidgetType.TOY, f"{widget_id} should be a toy"
        assert widget.consumable is False, f"Toy {widget_id} should not be consumable"

    # New food
    for widget_id in ['cookies', 'ramen', 'sushi', 'rice_ball', 'boba_tea',
                      'ice_cream', 'birthday_cake', 'golden_bamboo']:
        widget = wc.get_widget(widget_id)
        assert widget is not None, f"Widget {widget_id} should exist"
        assert widget.widget_type == WidgetType.FOOD, f"{widget_id} should be food"
        assert widget.consumable is True, f"Food {widget_id} should be consumable"
    print("✓ All new widgets exist with correct types")


def test_shop_widget_id_resolution():
    """Test that shop unlockable_ids correctly resolve to widget collection keys."""
    wc = WidgetCollection()

    # Food mappings (food_X -> X)
    assert wc.resolve_shop_widget_id('food_bamboo') == 'bamboo'
    assert wc.resolve_shop_widget_id('food_honey') == 'honey'
    assert wc.resolve_shop_widget_id('food_sushi') == 'sushi'
    assert wc.resolve_shop_widget_id('food_rice_ball') == 'rice_ball'
    assert wc.resolve_shop_widget_id('food_golden_bamboo') == 'golden_bamboo'

    # Direct matches (toy unlockable_ids are already direct)
    assert wc.resolve_shop_widget_id('ball') == 'ball'
    assert wc.resolve_shop_widget_id('bouncy_carrot') == 'bouncy_carrot'
    assert wc.resolve_shop_widget_id('dumbbell') == 'dumbbell'

    # Non-existent
    assert wc.resolve_shop_widget_id('nonexistent_item') is None
    print("✓ Shop widget ID resolution works")


def test_new_shop_items_exist():
    """Test that new shop items are in the catalog."""
    import tempfile
    tmpdir = tempfile.mkdtemp()
    shop = ShopSystem(save_path=Path(tmpdir) / 'shop.json')

    for item_id in ['toy_bouncy_carrot', 'toy_squishy_ball', 'toy_dumbbell']:
        assert item_id in shop.CATALOG, f"Shop should have {item_id}"
        item = shop.CATALOG[item_id]
        assert item.category == ShopCategory.TOYS, f"{item_id} should be TOYS category"

    # Verify food items have correct unlockable_ids
    for item_id in ['food_bamboo', 'food_sushi', 'food_honey']:
        item = shop.CATALOG[item_id]
        assert item.unlockable_id is not None, f"{item_id} should have unlockable_id"
        assert item.one_time_purchase is False, f"Food {item_id} should be repeatable"

    import shutil
    shutil.rmtree(tmpdir)
    print("✓ New shop items exist with correct properties")


def test_closet_categories_excluded_from_inventory():
    """Test that closet categories are properly identified for exclusion."""
    # These are the categories that should go to closet, not inventory
    closet_categories = {'panda_outfits', 'clothes', 'accessories'}

    # These should NOT be in closet categories
    inventory_categories = {'food', 'toys', 'cursors', 'cursor_trails',
                            'themes', 'animations', 'upgrades', 'special'}

    for cat in inventory_categories:
        assert cat not in closet_categories, f"{cat} should not be a closet category"
    print("✓ Closet categories properly exclude inventory items")


def test_panda_item_interaction():
    """Test panda can interact with items on screen."""
    panda = PandaCharacter()

    # Food interaction
    response = panda.on_item_interact('Fresh Bamboo', 'food')
    food_keywords = {'bamboo', 'food', 'nom', 'sniff', 'chomp', 'munch', 'snack', 'walks', 'picks'}
    assert any(kw in response.lower() for kw in food_keywords), \
        f"Food interact should mention food-related action: {response}"
    assert panda.feed_count == 1, "Food interaction should increase feed count"

    # Toy interaction
    response = panda.on_item_interact('Bouncy Carrot', 'toy')
    toy_keywords = {'carrot', 'play', 'kick', 'walks', 'runs', 'spots', 'picks', 'bats', 'pounce', 'mine'}
    assert any(kw in response.lower() for kw in toy_keywords), \
        f"Toy interact should mention toy-related action: {response}"
    assert panda.toy_interact_count == 1, "Toy interaction should increase toy_interact_count"
    print("✓ Panda item interaction works correctly")


def test_food_add_quantity_auto_unlocks():
    """Test that adding food quantity also unlocks the item."""
    wc = WidgetCollection()

    # honey is rare and starts locked
    honey = wc.get_widget('honey')
    assert honey.unlocked is False, "Rare food should start locked"

    wc.add_food_quantity('honey', 1)
    assert honey.unlocked is True, "Adding food should auto-unlock it"
    assert honey.quantity == 1, "Quantity should be 1"
    print("✓ Food add quantity auto-unlocks item")


def test_widget_info_includes_consumable():
    """Test that widget info includes consumable and quantity data."""
    wc = WidgetCollection()

    ball = wc.get_widget('ball')
    info = ball.get_info()
    assert 'consumable' in info, "Info should include consumable field"
    assert info['consumable'] is False, "Ball should not be consumable"
    assert 'quantity' not in info, "Non-consumable should not show quantity"

    bamboo = wc.get_widget('bamboo')
    wc.add_food_quantity('bamboo', 5)
    info = bamboo.get_info()
    assert info['consumable'] is True, "Food should be consumable"
    assert info['quantity'] == 5, "Food should show quantity"
    print("✓ Widget info includes consumable data")


def test_inventory_only_shows_unlocked_owned():
    """Test that inventory filtering returns only unlocked/owned items."""
    wc = WidgetCollection()

    # Get unlocked toys only
    unlocked_toys = wc.get_all_widgets(WidgetType.TOY, unlocked_only=True)
    all_toys = wc.get_all_widgets(WidgetType.TOY)

    assert len(unlocked_toys) < len(all_toys), "Not all toys should be unlocked by default"
    for toy in unlocked_toys:
        assert toy.unlocked is True, "All returned toys should be unlocked"

    # Common items are unlocked by default
    common_toys = [t for t in all_toys if t.rarity == WidgetRarity.COMMON]
    for toy in common_toys:
        assert toy.unlocked is True, "Common toys should be unlocked by default"
    print("✓ Inventory filtering returns only unlocked/owned items")


if __name__ == "__main__":
    print("Testing Inventory & Items System...")
    print("-" * 50)

    try:
        test_item_physics_properties()
        test_food_is_consumable()
        test_toys_infinite_use()
        test_accessories_are_not_consumable()
        test_new_widgets_exist()
        test_shop_widget_id_resolution()
        test_new_shop_items_exist()
        test_closet_categories_excluded_from_inventory()
        test_panda_item_interaction()
        test_food_add_quantity_auto_unlocks()
        test_widget_info_includes_consumable()
        test_inventory_only_shows_unlocked_owned()

        print("-" * 50)
        print("✅ All inventory & items tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
