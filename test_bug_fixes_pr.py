"""
Test suite for bug fixes in this PR.
Tests panda widget crash fix, achievement triggers, shop items, cursor mappings, and closet integration.
"""

import unittest
import sys
import os
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.features.panda_character import PandaCharacter, PandaMood
from src.features.achievements import AchievementSystem
from src.features.shop_system import ShopSystem, ShopCategory
from src.features.panda_closet import PandaCloset


class TestPandaCharacterDeadlockFix(unittest.TestCase):
    """Test that PandaCharacter uses RLock to avoid deadlock on click."""

    def setUp(self):
        self.panda = PandaCharacter()

    def test_lock_is_reentrant(self):
        """Test that the lock is an RLock (reentrant)."""
        self.assertIsInstance(self.panda._lock, type(threading.RLock()))

    def test_on_click_does_not_deadlock(self):
        """Test that clicking the panda past the rage threshold doesn't deadlock."""
        # The rage mode triggers set_mood() which re-acquires the lock
        # With threading.Lock() this would deadlock; with RLock() it works
        for i in range(PandaCharacter.RAGE_CLICK_THRESHOLD + 5):
            response = self.panda.on_click()
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)

    def test_rage_mode_triggers_at_threshold(self):
        """Test that clicking enough times triggers rage mode."""
        for i in range(PandaCharacter.RAGE_CLICK_THRESHOLD - 1):
            self.panda.on_click()
        
        # The threshold click should trigger rage
        response = self.panda.on_click()
        self.assertIn('RAGE', response.upper())
        self.assertEqual(self.panda.current_mood, PandaMood.RAGE)

    def test_track_file_processed_no_deadlock(self):
        """Test that processing 10000+ files doesn't deadlock."""
        # At 10000 files, set_mood is called while holding the lock
        self.panda.files_processed_count = 9999
        self.panda.track_file_processed()  # Should not deadlock
        self.assertEqual(self.panda.current_mood, PandaMood.EXISTENTIAL)

    def test_track_operation_failure_no_deadlock(self):
        """Test that multiple failures don't deadlock."""
        for i in range(10):
            self.panda.track_operation_failure()
        self.assertEqual(self.panda.current_mood, PandaMood.RAGE)

    def test_on_pet_returns_response(self):
        """Test petting the panda returns a valid response."""
        response = self.panda.on_pet()
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertEqual(self.panda.pet_count, 1)

    def test_on_feed_returns_response(self):
        """Test feeding the panda returns a valid response."""
        response = self.panda.on_feed()
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertEqual(self.panda.feed_count, 1)


class TestAchievementMarathonFix(unittest.TestCase):
    """Test that marathon achievement now triggers correctly."""

    def setUp(self):
        self.achievements = AchievementSystem()

    def test_marathon_achievement_increments(self):
        """Test that increment_session_time actually updates marathon progress."""
        marathon = self.achievements.get_achievement('marathon')
        self.assertIsNotNone(marathon)
        initial_progress = marathon.progress

        self.achievements.increment_session_time(60)  # 60 minutes
        
        marathon = self.achievements.get_achievement('marathon')
        self.assertGreater(marathon.progress, initial_progress)

    def test_marathon_achievement_unlocks(self):
        """Test that marathon unlocks after 240 minutes."""
        marathon = self.achievements.get_achievement('marathon')
        self.assertFalse(marathon.unlocked)

        # Simulate 240 minutes (4 hours)
        self.achievements.increment_session_time(240)
        
        marathon = self.achievements.get_achievement('marathon')
        self.assertTrue(marathon.unlocked)

    def test_dedicated_achievement_tracks_sessions(self):
        """Test that sessions are tracked for the dedicated achievement."""
        for _ in range(10):
            self.achievements.increment_sessions()
        
        dedicated = self.achievements.get_achievement('dedicated')
        self.assertTrue(dedicated.unlocked)

    def test_textures_sorted_achievements(self):
        """Test that sorting textures updates progress achievements."""
        self.achievements.increment_textures_sorted(1)
        
        first_sort = self.achievements.get_achievement('first_sort')
        self.assertTrue(first_sort.unlocked)


class TestShopNewItems(unittest.TestCase):
    """Test that new shop items are available."""

    def setUp(self):
        self.shop = ShopSystem()

    def test_new_outfits_exist(self):
        """Test that new outfit items are in the catalog."""
        self.assertIn('panda_chef', self.shop.CATALOG)
        self.assertIn('panda_detective', self.shop.CATALOG)
        self.assertIn('panda_superhero', self.shop.CATALOG)

    def test_new_cursors_exist(self):
        """Test that new cursor items are in the catalog."""
        self.assertIn('cursor_star', self.shop.CATALOG)
        self.assertIn('cursor_diamond', self.shop.CATALOG)

    def test_new_themes_exist(self):
        """Test that new theme items are in the catalog."""
        self.assertIn('theme_retro', self.shop.CATALOG)
        self.assertIn('theme_ocean', self.shop.CATALOG)

    def test_new_animations_exist(self):
        """Test that new animation items are in the catalog."""
        self.assertIn('anim_spin', self.shop.CATALOG)
        self.assertIn('anim_juggle', self.shop.CATALOG)

    def test_new_special_items_exist(self):
        """Test that new special items are in the catalog."""
        self.assertIn('special_party_hat', self.shop.CATALOG)
        self.assertIn('special_rainbow_aura', self.shop.CATALOG)
        self.assertIn('upgrade_lucky_charm', self.shop.CATALOG)

    def test_total_item_count_increased(self):
        """Test that total shop items increased from original 18 to 30."""
        self.assertGreaterEqual(len(self.shop.CATALOG), 30)

    def test_items_by_category(self):
        """Test that items are correctly categorized."""
        outfits = self.shop.get_items_by_category(ShopCategory.PANDA_OUTFITS, user_level=100)
        self.assertGreaterEqual(len(outfits), 8)  # 5 original + 3 new
        
        cursors = self.shop.get_items_by_category(ShopCategory.CURSORS, user_level=100)
        self.assertGreaterEqual(len(cursors), 5)  # 3 original + 2 new

    def test_new_items_purchasable(self):
        """Test that new items can be checked for purchase."""
        can_buy, reason = self.shop.can_purchase('panda_chef', 1000)
        self.assertTrue(can_buy)
        
        can_buy, reason = self.shop.can_purchase('panda_chef', 10)
        self.assertFalse(can_buy)


class TestPandaClosetAvailable(unittest.TestCase):
    """Test that PandaCloset is properly available."""

    def test_closet_initializes(self):
        """Test that PandaCloset can be initialized."""
        closet = PandaCloset()
        self.assertIsNotNone(closet)

    def test_closet_has_items(self):
        """Test that PandaCloset has default items."""
        closet = PandaCloset()
        stats = closet.get_statistics()
        self.assertGreater(stats['total_items'], 0)


class TestPandaCharacterAnimations(unittest.TestCase):
    """Test panda animation frames don't crash."""

    def setUp(self):
        self.panda = PandaCharacter()

    def test_get_animation_frame_valid(self):
        """Test getting animation frames for all known animations."""
        for anim_name in PandaCharacter.ANIMATIONS:
            frame = self.panda.get_animation_frame(anim_name)
            self.assertIsNotNone(frame)
            self.assertIsInstance(frame, str)

    def test_get_animation_frame_unknown_falls_back(self):
        """Test that unknown animation name falls back to idle."""
        frame = self.panda.get_animation_frame('nonexistent_animation')
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, str)

    def test_context_menu_returns_valid_dict(self):
        """Test that context menu returns valid actions."""
        menu = self.panda.get_context_menu()
        self.assertIn('pet_panda', menu)
        self.assertIn('feed_bamboo', menu)
        self.assertIn('check_mood', menu)

    def test_mood_indicator_for_all_moods(self):
        """Test mood indicator works for all mood states."""
        for mood in PandaMood:
            self.panda.set_mood(mood)
            indicator = self.panda.get_mood_indicator()
            self.assertIsNotNone(indicator)
            self.assertIsInstance(indicator, str)


if __name__ == '__main__':
    unittest.main()
