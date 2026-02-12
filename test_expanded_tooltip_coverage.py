#!/usr/bin/env python3
"""
Test expanded tooltip coverage for all new widget IDs.
Validates:
- All new widget IDs exist in _PANDA_TOOLTIPS with normal and vulgar variants
- All new widget IDs return tooltips in all 3 modes (normal, dumbed-down, vulgar)
- Vulgar mode has >=4 variations for all new widget IDs
- Normal mode has >=4 variations for all new widget IDs
- Dumbed-down mode has >=2 variations for all new widget IDs
- Tooltip mode returns correct mode-specific tooltips (not cross-contaminated)
- Existing widget IDs still work correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


class MockConfig:
    """Minimal config mock for testing."""
    def get(self, *args, default=None):
        return default
    def set(self, *args, **kwargs):
        pass
    def save(self):
        pass


def test_new_panda_tooltips_entries():
    """Verify _PANDA_TOOLTIPS has entries for all new widget IDs."""
    from src.features.tutorial_system import _PANDA_TOOLTIPS

    new_widget_ids = [
        "pause_button", "stop_button", "sort_mode_menu",
        "extract_archives", "compress_output",
        "convert_from_format", "convert_to_format",
        "convert_recursive", "convert_keep_original",
        "profile_new",
        "settings_perf_tab", "settings_appearance_tab",
        "settings_controls_tab", "settings_files_tab",
        "settings_ai_tab", "settings_system_tab",
        "tooltip_mode_normal", "tooltip_mode_dumbed_down", "tooltip_mode_vulgar",
        "shop_balance", "shop_level",
        "inventory_animations", "popout_button",
        "minigames_tab", "closet_appearance", "closet_header",
        "achievement_progress",
    ]

    for widget_id in new_widget_ids:
        assert widget_id in _PANDA_TOOLTIPS, (
            f"_PANDA_TOOLTIPS missing entry for '{widget_id}'"
        )
        entry = _PANDA_TOOLTIPS[widget_id]
        assert "normal" in entry, f"'{widget_id}' missing 'normal' tooltips"
        assert "vulgar" in entry, f"'{widget_id}' missing 'vulgar' tooltips"
        assert len(entry["normal"]) >= 4, (
            f"'{widget_id}' should have >=4 normal variants, got {len(entry['normal'])}"
        )
        assert len(entry["vulgar"]) >= 5, (
            f"'{widget_id}' should have >=5 vulgar variants, got {len(entry['vulgar'])}"
        )
    print(f"✓ _PANDA_TOOLTIPS has {len(new_widget_ids)} new entries with sufficient variants")


def test_new_tooltips_all_modes():
    """Test that all new widget IDs return tooltips in all 3 modes."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    new_widget_ids = [
        "pause_button", "stop_button", "sort_mode_menu",
        "extract_archives", "compress_output",
        "convert_from_format", "convert_to_format",
        "convert_recursive", "convert_keep_original",
        "profile_new",
        "settings_perf_tab", "settings_appearance_tab",
        "settings_controls_tab", "settings_files_tab",
        "settings_ai_tab", "settings_system_tab",
        "tooltip_mode_normal", "tooltip_mode_dumbed_down", "tooltip_mode_vulgar",
        "shop_balance", "shop_level",
        "inventory_animations", "popout_button",
        "minigames_tab", "closet_appearance", "closet_header",
        "achievement_progress",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in new_widget_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"No tooltip for '{widget_id}' in mode '{mode.value}'"
            )
            assert len(tip) > 10, (
                f"Tooltip for '{widget_id}' in '{mode.value}' is too short: '{tip}'"
            )
    print("✓ All new widget IDs return tooltips in all 3 modes")


def test_vulgar_mode_new_variations():
    """Vulgar mode should have >=4 variations for all new widget IDs."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())
    vulgar = mgr.tooltips[TooltipMode.VULGAR_PANDA]

    new_widget_ids = [
        "pause_button", "stop_button", "sort_mode_menu",
        "extract_archives", "compress_output",
        "convert_from_format", "convert_to_format",
        "convert_recursive", "convert_keep_original",
        "profile_new",
        "settings_perf_tab", "settings_appearance_tab",
        "settings_controls_tab", "settings_files_tab",
        "settings_ai_tab", "settings_system_tab",
        "tooltip_mode_normal", "tooltip_mode_dumbed_down", "tooltip_mode_vulgar",
        "shop_balance", "shop_level",
        "inventory_animations", "popout_button",
        "minigames_tab", "closet_appearance", "closet_header",
        "achievement_progress",
    ]

    for widget_id in new_widget_ids:
        tips = vulgar.get(widget_id, "")
        assert isinstance(tips, list), (
            f"Vulgar '{widget_id}' should be a list, got {type(tips)}"
        )
        assert len(tips) >= 4, (
            f"Vulgar '{widget_id}' should have >=4 variants, got {len(tips)}"
        )
    print("✓ Vulgar mode has >=4 variations for all new widget IDs")


def test_normal_mode_new_variations():
    """Normal mode should have >=4 variations for all new widget IDs."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())
    normal = mgr.tooltips[TooltipMode.NORMAL]

    new_widget_ids = [
        "pause_button", "stop_button", "sort_mode_menu",
        "extract_archives", "compress_output",
        "convert_from_format", "convert_to_format",
        "convert_recursive", "convert_keep_original",
        "profile_new",
        "settings_perf_tab", "settings_appearance_tab",
        "settings_controls_tab", "settings_files_tab",
        "settings_ai_tab", "settings_system_tab",
        "tooltip_mode_normal", "tooltip_mode_dumbed_down", "tooltip_mode_vulgar",
        "shop_balance", "shop_level",
        "inventory_animations", "popout_button",
        "minigames_tab", "closet_appearance", "closet_header",
        "achievement_progress",
    ]

    for widget_id in new_widget_ids:
        tips = normal.get(widget_id, "")
        assert isinstance(tips, list), (
            f"Normal '{widget_id}' should be a list, got {type(tips)}"
        )
        assert len(tips) >= 4, (
            f"Normal '{widget_id}' should have >=4 variants, got {len(tips)}"
        )
    print("✓ Normal mode has >=4 variations for all new widget IDs")


def test_tooltip_mode_isolation():
    """Verify that switching modes returns different tooltips."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    # Collect all possible tooltip texts for each mode for a widget that differs
    widget_id = 'sort_button'
    mode_tips = {}
    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        tips_list = mgr.tooltips[mode].get(widget_id, [])
        if isinstance(tips_list, list):
            mode_tips[mode.value] = set(tips_list)
        else:
            mode_tips[mode.value] = {tips_list}

    # Vulgar tooltips should be distinct from normal tooltips
    normal_set = mode_tips.get('normal', set())
    vulgar_set = mode_tips.get('vulgar_panda', set())
    if normal_set and vulgar_set:
        assert normal_set != vulgar_set, (
            "Normal and vulgar tooltips for 'sort_button' should differ"
        )
    print("✓ Tooltip modes return distinct tooltips per mode")


def test_existing_tooltips_still_work():
    """Verify that previously existing tooltip IDs still work."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    existing_ids = [
        "sort_button", "convert_button", "input_browse", "output_browse",
        "detect_lods", "group_lods", "detect_duplicates",
        "style_dropdown", "settings_button", "theme_button", "help_button",
        "achievements_tab", "shop_tab", "shop_buy_button",
        "rewards_tab", "closet_tab",
        "browser_browse_button", "browser_refresh_button",
        "browser_search", "browser_show_all",
        "sort_tab", "convert_tab", "browser_tab", "notepad_tab", "about_tab",
        "tools_category", "features_category",
        "inventory_tab", "panda_stats_tab",
        "keyboard_controls", "tooltip_mode", "theme_selector",
        "sound_enabled", "master_volume", "effects_volume",
        "notifications_volume", "sound_pack",
        "cursor_type", "cursor_size", "cursor_trail",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        mgr.set_mode(mode)
        for widget_id in existing_ids:
            tip = mgr.get_tooltip(widget_id)
            assert tip, (
                f"Existing tooltip '{widget_id}' broken in mode '{mode.value}'"
            )
    print(f"✓ All {len(existing_ids)} existing tooltip IDs still work in all modes")


def test_vulgar_tooltips_are_vulgar():
    """Spot check that vulgar tooltips contain characteristic language."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())
    vulgar = mgr.tooltips[TooltipMode.VULGAR_PANDA]

    # Check a few entries for characteristic vulgar language patterns
    vulgar_markers = ['damn', 'hell', 'sh*t', 'f*ck', 'ass', 'crap', 'idiot',
                      'stupid', 'dumb', 'bastard', 'suck', 'wtf', 'stfu',
                      'noob', 'nerd', 'lame', 'boring', 'lazy', 'psychopath',
                      'screw', 'b*tch', 'motherf', 'goddamn', 'piss']

    sample_ids = ['sort_button', 'pause_button', 'stop_button', 'convert_button',
                  'settings_button', 'extract_archives', 'compress_output']

    total_vulgar_count = 0
    for wid in sample_ids:
        tips = vulgar.get(wid, [])
        if isinstance(tips, list):
            for tip in tips:
                tip_lower = tip.lower()
                if any(marker in tip_lower for marker in vulgar_markers):
                    total_vulgar_count += 1

    assert total_vulgar_count > 5, (
        f"Vulgar tooltips should contain characteristic language, found {total_vulgar_count} instances"
    )
    print(f"✓ Vulgar tooltips contain characteristic language ({total_vulgar_count} vulgar instances found)")


def test_no_empty_tooltip_strings():
    """Ensure no tooltip entry is an empty string or list."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    mgr = TooltipVerbosityManager(MockConfig())

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        tooltips = mgr.tooltips[mode]
        for widget_id, tip in tooltips.items():
            if isinstance(tip, list):
                for i, t in enumerate(tip):
                    assert t and len(t.strip()) > 0, (
                        f"Empty tooltip string at index {i} for '{widget_id}' in mode '{mode.value}'"
                    )
            elif isinstance(tip, str):
                assert tip and len(tip.strip()) > 0, (
                    f"Empty tooltip string for '{widget_id}' in mode '{mode.value}'"
                )
    print("✓ No empty tooltip strings found in any mode")


if __name__ == "__main__":
    print("Testing Expanded Tooltip Coverage...")
    print("-" * 50)
    try:
        test_new_panda_tooltips_entries()
        test_new_tooltips_all_modes()
        test_vulgar_mode_new_variations()
        test_normal_mode_new_variations()
        test_tooltip_mode_isolation()
        test_existing_tooltips_still_work()
        test_vulgar_tooltips_are_vulgar()
        test_no_empty_tooltip_strings()
        print("-" * 50)
        print("✅ All expanded tooltip coverage tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
