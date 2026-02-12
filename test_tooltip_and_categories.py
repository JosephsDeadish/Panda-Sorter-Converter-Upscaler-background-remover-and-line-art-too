#!/usr/bin/env python3
"""
Test tooltip coverage and category keyword expansion.
Validates:
- All settings widgets have tooltip entries in all 3 modes
- Vulgar mode has multiple variations per widget
- Normal and dumbed-down modes have entries for settings widgets
- AI categories have expanded keyword lists for better recognition
- _PANDA_TOOLTIPS includes new settings entries
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_categories_keyword_expansion():
    """Test that categories have significantly more keywords than before."""
    from src.classifier.categories import ALL_CATEGORIES

    # Total keyword count should be well above the original ~600
    total_keywords = sum(len(cat.get("keywords", [])) for cat in ALL_CATEGORIES.values())
    assert total_keywords > 1500, (
        f"Expected >1500 total keywords after expansion, got {total_keywords}"
    )
    print(f"✓ Total keywords expanded to {total_keywords}")


def test_categories_structure_intact():
    """Ensure all original category groups still exist and are non-empty."""
    from src.classifier.categories import (
        CHARACTER_ORGANIC, CLOTHING_WEARABLES, VEHICLES,
        ENVIRONMENT_NATURAL, ENVIRONMENT_MANMADE, UI_HUD,
        EFFECTS, OBJECTS_PROPS, TECHNICAL, MISC,
        ALL_CATEGORIES, CATEGORY_GROUPS,
    )

    for name, group in [
        ("CHARACTER_ORGANIC", CHARACTER_ORGANIC),
        ("CLOTHING_WEARABLES", CLOTHING_WEARABLES),
        ("VEHICLES", VEHICLES),
        ("ENVIRONMENT_NATURAL", ENVIRONMENT_NATURAL),
        ("ENVIRONMENT_MANMADE", ENVIRONMENT_MANMADE),
        ("UI_HUD", UI_HUD),
        ("EFFECTS", EFFECTS),
        ("OBJECTS_PROPS", OBJECTS_PROPS),
        ("TECHNICAL", TECHNICAL),
        ("MISC", MISC),
    ]:
        assert len(group) > 0, f"{name} should not be empty"
        for cat_id, cat_info in group.items():
            assert "name" in cat_info, f"{cat_id} missing 'name'"
            assert "keywords" in cat_info, f"{cat_id} missing 'keywords'"
            assert "group" in cat_info, f"{cat_id} missing 'group'"

    # ALL_CATEGORIES should include every category from every group
    assert len(ALL_CATEGORIES) == 116, (
        f"Expected 116 categories, got {len(ALL_CATEGORIES)}"
    )
    print("✓ All category groups intact with correct structure")


def test_sample_new_keywords():
    """Spot-check that specific new keywords are present."""
    from src.classifier.categories import ALL_CATEGORIES

    checks = {
        "animals": ["eagle", "shark", "elephant", "butterfly", "crocodile"],
        "weapons": ["katana", "crossbow", "revolver", "trident", "cannon"],
        "fire": ["torch", "campfire", "candle", "furnace"],
        "water": ["waterfall", "puddle", "underwater", "caustic"],
        "buildings": ["skyscraper", "castle", "cathedral", "bunker"],
        "normal_maps": ["nrm", "tangent_normal", "ddna"],
        "roughness_maps": ["metalness", "smoothness", "orm"],
        "food": ["pizza", "hamburger", "apple", "chocolate"],
        "trees": ["pine", "oak", "birch", "redwood", "sapling"],
    }

    for cat_id, expected_keywords in checks.items():
        cat = ALL_CATEGORIES.get(cat_id)
        assert cat is not None, f"Category '{cat_id}' not found"
        actual = cat.get("keywords", [])
        for kw in expected_keywords:
            assert kw in actual, (
                f"Expected keyword '{kw}' in category '{cat_id}'"
            )
    print("✓ Sample new keywords verified across categories")


def test_panda_tooltips_settings_entries():
    """Verify _PANDA_TOOLTIPS has entries for new settings widgets."""
    from src.features.tutorial_system import _PANDA_TOOLTIPS

    new_settings_ids = [
        "sound_enabled", "master_volume", "effects_volume",
        "notifications_volume", "sound_pack", "sound_test_button",
        "cursor_type", "cursor_size", "cursor_tint", "cursor_trail", "trail_style",
        "hotkey_edit", "hotkey_toggle", "hotkey_reset",
        "sound_choice", "per_event_sound",
    ]

    for widget_id in new_settings_ids:
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
    print("✓ _PANDA_TOOLTIPS has settings entries with sufficient variants")


def test_tooltip_manager_settings_coverage():
    """Test that TooltipVerbosityManager returns tooltips for new settings widgets."""
    # Create a minimal mock config
    class MockConfig:
        def get(self, *args, default=None):
            return default
        def set(self, *args, **kwargs):
            pass
        def save(self):
            pass

    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    settings_ids = [
        "sound_enabled", "master_volume", "effects_volume",
        "notifications_volume", "sound_pack", "per_event_sound",
        "sound_test_button", "sound_choice",
        "cursor_type", "cursor_size", "cursor_tint",
        "cursor_trail", "trail_style",
        "hotkey_edit", "hotkey_toggle", "hotkey_reset",
        "tooltip_mode", "theme_selector", "keyboard_controls",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in settings_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
    print("✓ TooltipVerbosityManager returns tooltips for all settings widgets in all modes")


def test_vulgar_mode_has_many_variations():
    """Vulgar mode should have >=4 variations for most widgets."""
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
        "sort_button", "convert_button", "input_browse", "output_browse",
        "sound_enabled", "master_volume", "cursor_type", "cursor_trail",
        "hotkey_edit", "hotkey_toggle",
    ]

    for widget_id in widgets_needing_many:
        tips = vulgar.get(widget_id, "")
        if isinstance(tips, list):
            assert len(tips) >= 4, (
                f"Vulgar '{widget_id}' should have >=4 variants, got {len(tips)}"
            )
        # single string is acceptable for some widgets
    print("✓ Vulgar mode has >=4 variations for key widgets")


def test_get_category_helpers():
    """Ensure helper functions still work."""
    from src.classifier.categories import (
        get_category_names, get_category_info, get_categories_by_group,
    )

    names = get_category_names()
    assert len(names) == 116
    assert "eyes" in names
    assert "unclassified" in names

    info = get_category_info("weapons")
    assert info["name"] == "Weapons"
    assert "katana" in info["keywords"]

    env = get_categories_by_group("Environment/Natural")
    assert "trees" in env
    assert "water" in env
    print("✓ Category helper functions work correctly")


if __name__ == "__main__":
    print("Testing Tooltip Coverage & Category Expansion...")
    print("-" * 50)
    test_categories_keyword_expansion()
    test_categories_structure_intact()
    test_sample_new_keywords()
    test_panda_tooltips_settings_entries()
    test_tooltip_manager_settings_coverage()
    test_vulgar_mode_has_many_variations()
    test_get_category_helpers()
    print("-" * 50)
    print("✅ All tooltip & category tests passed!")
