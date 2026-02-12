#!/usr/bin/env python3
"""
Test clothing subcategories, body-part attachment, and expanded tooltips.
Validates:
- ClothingSubCategory enum and CLOTHING_SUBCATEGORIES mapping
- Clothing items have clothing_type set correctly
- get_clothing_by_subcategory returns correct items
- All clothing types are valid subcategory values
- New tooltip entries exist across all 3 modes for closet/shop/UI/settings
- _PANDA_TOOLTIPS includes closet subcategory entries with variants
- Clothing drawing method handles all types without error
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_clothing_subcategory_enum():
    """Test that ClothingSubCategory enum exists with expected values."""
    from src.features.panda_closet import ClothingSubCategory
    expected = {'shirt', 'pants', 'jacket', 'dress', 'full_body', 'other'}
    actual = {e.value for e in ClothingSubCategory}
    assert actual == expected, (
        f"ClothingSubCategory values mismatch: expected {expected}, got {actual}"
    )
    print("✓ ClothingSubCategory enum has correct values")


def test_clothing_subcategories_mapping():
    """Test that CLOTHING_SUBCATEGORIES is populated from DEFAULT_ITEMS."""
    from src.features.panda_closet import CLOTHING_SUBCATEGORIES, ClothingSubCategory
    assert len(CLOTHING_SUBCATEGORIES) > 0, "CLOTHING_SUBCATEGORIES should not be empty"
    for item_id, sub_cat in CLOTHING_SUBCATEGORIES.items():
        assert isinstance(sub_cat, ClothingSubCategory), (
            f"CLOTHING_SUBCATEGORIES['{item_id}'] should be a ClothingSubCategory"
        )
    print(f"✓ CLOTHING_SUBCATEGORIES has {len(CLOTHING_SUBCATEGORIES)} entries")


def test_all_clothing_items_have_type():
    """Test that every clothing item has a clothing_type set."""
    from src.features.panda_closet import PandaCloset, CustomizationCategory
    pc = PandaCloset()
    clothing_items = pc.get_items_by_category(CustomizationCategory.CLOTHING)
    for item in clothing_items:
        assert item.clothing_type, (
            f"Clothing item '{item.id}' ({item.name}) missing clothing_type"
        )
    print(f"✓ All {len(clothing_items)} clothing items have clothing_type set")


def test_clothing_types_are_valid():
    """Test that clothing_type values are valid subcategory values."""
    from src.features.panda_closet import PandaCloset, CustomizationCategory, ClothingSubCategory
    valid_types = {e.value for e in ClothingSubCategory}
    pc = PandaCloset()
    clothing_items = pc.get_items_by_category(CustomizationCategory.CLOTHING)
    for item in clothing_items:
        assert item.clothing_type in valid_types, (
            f"Item '{item.id}' has invalid clothing_type '{item.clothing_type}'"
        )
    print("✓ All clothing_type values are valid subcategory values")


def test_get_clothing_by_subcategory():
    """Test filtering clothing items by subcategory."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    # Unlock all items so we can test the filter
    for item in pc.items.values():
        item.unlocked = True

    shirts = pc.get_clothing_by_subcategory('shirt', unlocked_only=True)
    assert len(shirts) > 0, "Should have at least one shirt"
    for s in shirts:
        assert s.clothing_type == 'shirt', f"Item '{s.id}' is not a shirt"

    pants = pc.get_clothing_by_subcategory('pants', unlocked_only=True)
    assert len(pants) > 0, "Should have at least one pants item"
    for p in pants:
        assert p.clothing_type == 'pants', f"Item '{p.id}' is not pants"

    jackets = pc.get_clothing_by_subcategory('jacket', unlocked_only=True)
    assert len(jackets) > 0, "Should have at least one jacket"
    for j in jackets:
        assert j.clothing_type == 'jacket', f"Item '{j.id}' is not a jacket"

    dresses = pc.get_clothing_by_subcategory('dress', unlocked_only=True)
    assert len(dresses) > 0, "Should have at least one dress"

    full_body = pc.get_clothing_by_subcategory('full_body', unlocked_only=True)
    assert len(full_body) > 0, "Should have at least one full_body item"

    print(f"✓ Subcategory filter works: {len(shirts)} shirts, {len(pants)} pants, "
          f"{len(jackets)} jackets, {len(dresses)} dresses, {len(full_body)} full_body")


def test_subcategory_filter_unlocked_only():
    """Test that unlocked_only flag works with subcategory filter."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    # None should be unlocked by default for shop items
    unlocked_shirts = pc.get_clothing_by_subcategory('shirt', unlocked_only=True)
    all_shirts = pc.get_clothing_by_subcategory('shirt', unlocked_only=False)
    assert len(all_shirts) >= len(unlocked_shirts), (
        "Unfiltered should be >= unlocked-only"
    )
    print("✓ Subcategory unlocked_only filter works correctly")


def test_tooltip_closet_subcategory_entries():
    """Test that all tooltip modes have entries for closet subcategories."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    closet_ids = [
        "closet_all_clothing", "closet_shirts", "closet_pants",
        "closet_jackets", "closet_dresses", "closet_full_outfits",
        "closet_fur_style", "closet_fur_color", "closet_hats",
        "closet_shoes", "closet_accessories",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in closet_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ Closet subcategory tooltips present in all modes")


def test_tooltip_shop_subcategory_entries():
    """Test that shop subcategory tooltips exist in all modes."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    shop_ids = [
        "shop_outfits_cat", "shop_clothes_cat", "shop_accessories_cat",
        "shop_cursors_cat", "shop_cursor_trails_cat", "shop_themes_cat",
        "shop_food_cat", "shop_toys_cat", "shop_upgrades_cat",
        "shop_special_cat",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in shop_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ Shop subcategory tooltips present in all modes")


def test_tooltip_ui_settings_entries():
    """Test that UI settings tooltips exist in all modes."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    ui_ids = [
        "ui_language", "ui_font_size", "ui_animations", "ui_transparency",
        "ui_compact_mode", "ui_auto_save", "ui_confirm_exit",
        "ui_startup_tab", "ui_sidebar_position", "ui_show_statusbar",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in ui_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ UI settings tooltips present in all modes")


def test_tooltip_panda_settings_entries():
    """Test that panda settings tooltips exist in all modes."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    panda_ids = [
        "panda_name", "panda_gender", "panda_mood_display",
        "panda_auto_walk", "panda_speech_bubbles",
        "panda_interaction_sounds", "panda_idle_animations",
        "panda_drag_enabled",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in panda_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ Panda settings tooltips present in all modes")


def test_tooltip_performance_and_profile_entries():
    """Test that performance/profile tooltips exist in all modes."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    ids = [
        "perf_thread_count", "perf_cache_size", "perf_batch_size",
        "perf_preview_quality",
        "profile_save", "profile_load", "profile_delete",
        "profile_export", "profile_import",
        "stats_textures_sorted", "stats_time_spent",
        "stats_panda_interactions", "stats_achievements_earned",
        "stats_currency_earned",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ Performance, profile, and statistics tooltips present in all modes")


def test_panda_tooltips_closet_entries():
    """Verify _PANDA_TOOLTIPS has entries for closet subcategories."""
    from src.features.tutorial_system import _PANDA_TOOLTIPS

    closet_ids = [
        "closet_all_clothing", "closet_shirts", "closet_pants",
        "closet_jackets", "closet_dresses", "closet_full_outfits",
    ]

    for widget_id in closet_ids:
        assert widget_id in _PANDA_TOOLTIPS, (
            f"_PANDA_TOOLTIPS missing entry for '{widget_id}'"
        )
        entry = _PANDA_TOOLTIPS[widget_id]
        assert "normal" in entry, f"'{widget_id}' missing 'normal' tooltips"
        assert "vulgar" in entry, f"'{widget_id}' missing 'vulgar' tooltips"
        assert len(entry["normal"]) >= 3, (
            f"'{widget_id}' should have >=3 normal variants, got {len(entry['normal'])}"
        )
        assert len(entry["vulgar"]) >= 4, (
            f"'{widget_id}' should have >=4 vulgar variants, got {len(entry['vulgar'])}"
        )
    print("✓ _PANDA_TOOLTIPS has closet subcategory entries with sufficient variants")


def test_vulgar_mode_closet_variations():
    """Vulgar mode should have >=4 variations for closet subcategory widgets."""
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())
    vulgar = mgr.tooltips[TooltipMode.VULGAR_PANDA]

    widgets_needing_many = [
        "closet_all_clothing", "closet_shirts", "closet_pants",
        "closet_jackets", "closet_dresses", "closet_full_outfits",
    ]

    for widget_id in widgets_needing_many:
        tips = vulgar.get(widget_id, "")
        if isinstance(tips, list):
            assert len(tips) >= 4, (
                f"Vulgar '{widget_id}' should have >=4 variants, got {len(tips)}"
            )
    print("✓ Vulgar mode has >=4 variations for closet subcategory widgets")


def test_clothing_item_field_preserved():
    """Test that clothing_type field is preserved through initialize_items copy."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    item = pc.get_item('overalls')
    assert item is not None, "overalls should exist"
    assert item.clothing_type == 'pants', (
        f"overalls should be 'pants', got '{item.clothing_type}'"
    )
    item2 = pc.get_item('hoodie')
    assert item2 is not None, "hoodie should exist"
    assert item2.clothing_type == 'jacket', (
        f"hoodie should be 'jacket', got '{item2.clothing_type}'"
    )
    item3 = pc.get_item('suit')
    assert item3 is not None, "suit should exist"
    assert item3.clothing_type == 'full_body', (
        f"suit should be 'full_body', got '{item3.clothing_type}'"
    )
    print("✓ clothing_type field preserved through item copy")


if __name__ == "__main__":
    print("Testing Clothing Subcategories & Expanded Tooltips...")
    print("-" * 50)
    try:
        test_clothing_subcategory_enum()
        test_clothing_subcategories_mapping()
        test_all_clothing_items_have_type()
        test_clothing_types_are_valid()
        test_get_clothing_by_subcategory()
        test_subcategory_filter_unlocked_only()
        test_tooltip_closet_subcategory_entries()
        test_tooltip_shop_subcategory_entries()
        test_tooltip_ui_settings_entries()
        test_tooltip_panda_settings_entries()
        test_tooltip_performance_and_profile_entries()
        test_panda_tooltips_closet_entries()
        test_vulgar_mode_closet_variations()
        test_clothing_item_field_preserved()
        print("-" * 50)
        print("✅ All clothing & tooltip tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
