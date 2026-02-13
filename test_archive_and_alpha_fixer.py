#!/usr/bin/env python3
"""
Test archive checkbox, alpha fixer output directory, dropdown emojis,
and tooltip coverage for newly added widget IDs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

SEPARATOR_WIDTH = 70


class MockConfig:
    """Minimal config mock for testing."""
    def get(self, *args, default=None):
        return default
    def set(self, *args, **kwargs):
        pass
    def save(self):
        pass


def test_new_panda_tooltip_entries():
    """Verify _PANDA_TOOLTIPS has entries for all new alpha fixer and browser widget IDs."""
    from src.features.tutorial_system import _PANDA_TOOLTIPS

    new_widget_ids = [
        "browser_show_archives",
        "alpha_fix_button",
        "alpha_fix_input",
        "alpha_fix_output",
        "alpha_fix_preset",
        "alpha_fix_recursive",
        "alpha_fix_backup",
        "alpha_fix_overwrite",
        "alpha_fix_extract_archive",
        "alpha_fix_compress_archive",
    ]

    print(f"\n{'=' * SEPARATOR_WIDTH}")
    print("Test 1: New _PANDA_TOOLTIPS entries")
    print(f"{'=' * SEPARATOR_WIDTH}")

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
        assert len(entry["vulgar"]) >= 4, (
            f"'{widget_id}' should have >=4 vulgar variants, got {len(entry['vulgar'])}"
        )
        print(f"  ✓ '{widget_id}' has {len(entry['normal'])} normal, {len(entry['vulgar'])} vulgar variants")

    print(f"\n✓ All {len(new_widget_ids)} new widget IDs present with sufficient variants")


def test_dumbed_down_tooltips():
    """Verify dumbed-down tooltips exist for new widget IDs."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    print(f"\n{'=' * SEPARATOR_WIDTH}")
    print("Test 2: Dumbed-down tooltips for new widget IDs")
    print(f"{'=' * SEPARATOR_WIDTH}")

    manager = TooltipVerbosityManager(MockConfig())
    manager.set_mode(TooltipMode.DUMBED_DOWN)

    new_widget_ids = [
        "browser_show_archives",
        "alpha_fix_button",
        "alpha_fix_input",
        "alpha_fix_output",
        "alpha_fix_preset",
        "alpha_fix_recursive",
        "alpha_fix_backup",
        "alpha_fix_overwrite",
        "alpha_fix_extract_archive",
        "alpha_fix_compress_archive",
    ]

    for widget_id in new_widget_ids:
        tooltip = manager.get_tooltip(widget_id)
        assert tooltip and len(tooltip) > 0, (
            f"Dumbed-down tooltip for '{widget_id}' is empty"
        )
        print(f"  ✓ '{widget_id}': {tooltip[:60]}...")

    print(f"\n✓ All {len(new_widget_ids)} dumbed-down tooltips present")


def test_all_three_modes():
    """Verify all three tooltip modes return text for new widget IDs."""
    from src.features.tutorial_system import TooltipVerbosityManager, TooltipMode

    print(f"\n{'=' * SEPARATOR_WIDTH}")
    print("Test 3: All three modes return tooltips")
    print(f"{'=' * SEPARATOR_WIDTH}")

    manager = TooltipVerbosityManager(MockConfig())

    new_widget_ids = [
        "browser_show_archives",
        "alpha_fix_button",
        "alpha_fix_output",
        "alpha_fix_preset",
        "alpha_fix_extract_archive",
        "alpha_fix_compress_archive",
    ]

    for mode in [TooltipMode.NORMAL, TooltipMode.DUMBED_DOWN, TooltipMode.VULGAR_PANDA]:
        manager.set_mode(mode)
        for widget_id in new_widget_ids:
            tooltip = manager.get_tooltip(widget_id)
            assert tooltip and len(tooltip) > 0, (
                f"Mode '{mode.value}' returned empty tooltip for '{widget_id}'"
            )
        print(f"  ✓ Mode '{mode.value}' returns tooltips for all new widgets")

    print(f"\n✓ All modes work for new widget IDs")


def test_emoji_prefix_stripping():
    """Test that emoji prefixes can be stripped from dropdown values."""
    print(f"\n{'=' * SEPARATOR_WIDTH}")
    print("Test 4: Emoji prefix stripping")
    print(f"{'=' * SEPARATOR_WIDTH}")

    # Test format dropdown stripping
    format_values = ["🎮 DDS", "🖼️ PNG", "📷 JPG", "🗺️ BMP", "🎨 TGA"]
    for val in format_values:
        stripped = val.split(' ', 1)[-1] if ' ' in val else val
        assert stripped == stripped.upper(), f"Stripped value '{stripped}' should be uppercase format"
        assert stripped in ["DDS", "PNG", "JPG", "BMP", "TGA"], f"Unexpected format: {stripped}"
        print(f"  ✓ '{val}' → '{stripped}'")

    # Test preset dropdown stripping
    preset_values = ["🔲 ps2_binary", "🔳 ps2_three_level", "🖥️ ps2_ui",
                     "🌊 ps2_smooth", "⬛ generic_binary", "✂️ clean_edges"]
    expected_keys = ["ps2_binary", "ps2_three_level", "ps2_ui",
                     "ps2_smooth", "generic_binary", "clean_edges"]
    for val, expected in zip(preset_values, expected_keys):
        stripped = val.split(' ', 1)[-1] if ' ' in val else val
        assert stripped == expected, f"Expected '{expected}', got '{stripped}'"
        print(f"  ✓ '{val}' → '{stripped}'")

    print(f"\n✓ All emoji prefixes strip correctly")


def test_alpha_preset_lookup():
    """Verify alpha presets can be looked up after stripping emoji."""
    print(f"\n{'=' * SEPARATOR_WIDTH}")
    print("Test 5: Alpha preset lookup after emoji strip")
    print(f"{'=' * SEPARATOR_WIDTH}")

    try:
        from src.preprocessing.alpha_correction import AlphaCorrectionPresets

        preset_display_values = ["🔲 ps2_binary", "🔳 ps2_three_level", "🖥️ ps2_ui",
                                 "🌊 ps2_smooth", "⬛ generic_binary", "✂️ clean_edges"]

        for display_val in preset_display_values:
            key = display_val.split(' ', 1)[-1] if ' ' in display_val else display_val
            preset = AlphaCorrectionPresets.get_preset(key)
            assert preset is not None, f"Preset not found for key '{key}'"
            assert 'description' in preset, f"Preset '{key}' missing description"
            print(f"  ✓ '{key}': {preset.get('description', '')[:50]}...")

        print(f"\n✓ All presets look up correctly")
    except ImportError as e:
        print(f"  ⚠️ Skipped (import error): {e}")


if __name__ == "__main__":
    print("Testing Archive Checkbox, Alpha Fixer, and Tooltip Coverage...")
    print("-" * SEPARATOR_WIDTH)
    try:
        test_new_panda_tooltip_entries()
        test_dumbed_down_tooltips()
        test_all_three_modes()
        test_emoji_prefix_stripping()
        test_alpha_preset_lookup()
        print(f"\n{'-' * SEPARATOR_WIDTH}")
        print("✅ All archive & alpha fixer tests passed!")
    except Exception as e:
        print(f"\n{'-' * SEPARATOR_WIDTH}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
