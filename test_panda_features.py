"""
Test suite for new panda features
Tests mini-games, widgets, closet, and translation systems
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.features.minigame_system import (
    MiniGameManager, PandaClickGame, PandaMemoryGame, 
    PandaReflexGame, GameDifficulty
)
from src.features.panda_widgets import (
    WidgetCollection, ToyWidget, FoodWidget, WidgetType, WidgetRarity
)
from src.features.panda_closet import (
    PandaCloset, CustomizationCategory, ItemRarity
)
from src.features.translation_manager import (
    TranslationManager, Language, t
)


class TestMiniGameSystem(unittest.TestCase):
    """Test mini-game system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = MiniGameManager()
    
    def test_get_available_games(self):
        """Test getting available games."""
        games = self.manager.get_available_games()
        self.assertGreater(len(games), 0)
        self.assertTrue(any(g['id'] == 'click' for g in games))
    
    def test_start_click_game(self):
        """Test starting click game."""
        game = self.manager.start_game('click', GameDifficulty.EASY)
        self.assertIsNotNone(game)
        self.assertIsInstance(game, PandaClickGame)
        self.assertTrue(game.is_running)
    
    def test_click_game_mechanics(self):
        """Test click game mechanics."""
        game = PandaClickGame(GameDifficulty.EASY)
        game.start()
        
        # Simulate clicks
        for _ in range(10):
            self.assertTrue(game.on_click())
        
        self.assertEqual(game.clicks, 10)
        self.assertEqual(game.score, 10)
    
    def test_memory_game_initialization(self):
        """Test memory game initialization."""
        game = PandaMemoryGame(GameDifficulty.MEDIUM)
        game.start()
        
        self.assertEqual(len(game.cards), 16)  # 4x4 grid
        self.assertTrue(game.is_running)
    
    def test_statistics(self):
        """Test game statistics."""
        stats = self.manager.get_statistics()
        self.assertIn('total_games', stats)
        self.assertIn('total_xp_earned', stats)


class TestPandaWidgets(unittest.TestCase):
    """Test panda widget system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.collection = WidgetCollection()
    
    def test_collection_initialization(self):
        """Test widget collection initialization."""
        toys = self.collection.get_toys()
        food = self.collection.get_food()
        
        self.assertGreater(len(toys), 0)
        self.assertGreater(len(food), 0)
    
    def test_common_widgets_unlocked(self):
        """Test that common widgets are unlocked by default."""
        unlocked_toys = self.collection.get_toys(unlocked_only=True)
        self.assertGreater(len(unlocked_toys), 0)
    
    def test_unlock_widget(self):
        """Test unlocking a widget."""
        widget_id = 'plushie'
        widget = self.collection.get_widget(widget_id)
        
        if not widget.unlocked:
            self.assertTrue(self.collection.unlock_widget(widget_id))
            self.assertTrue(widget.unlocked)
    
    def test_use_widget(self):
        """Test using a widget."""
        widget_id = 'ball'  # Common toy, should be unlocked
        result = self.collection.use_widget(widget_id)
        
        self.assertIsNotNone(result)
        self.assertIn('happiness', result)
        self.assertIn('message', result)
        self.assertIn('animation', result)
    
    def test_widget_statistics(self):
        """Test widget collection statistics."""
        stats = self.collection.get_statistics()
        
        self.assertIn('total_widgets', stats)
        self.assertIn('unlocked_widgets', stats)
        self.assertIn('by_type', stats)


class TestPandaCloset(unittest.TestCase):
    """Test panda closet system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.closet = PandaCloset()
    
    def test_closet_initialization(self):
        """Test closet initialization."""
        fur_styles = self.closet.get_items_by_category(CustomizationCategory.FUR_STYLE)
        self.assertGreater(len(fur_styles), 0)
    
    def test_default_appearance(self):
        """Test default appearance."""
        appearance = self.closet.get_current_appearance()
        self.assertEqual(appearance.fur_style, 'classic')
        self.assertEqual(appearance.fur_color, 'black_white')
    
    def test_unlock_item(self):
        """Test unlocking an item."""
        item_id = 'fluffy'
        self.assertTrue(self.closet.unlock_item(item_id))
        
        item = self.closet.get_item(item_id)
        self.assertTrue(item.unlocked)
    
    def test_equip_item(self):
        """Test equipping an item."""
        # Unlock and equip
        item_id = 'fluffy'
        self.closet.unlock_item(item_id)
        self.assertTrue(self.closet.equip_item(item_id))
        
        item = self.closet.get_item(item_id)
        self.assertTrue(item.equipped)
        
        # Check appearance updated
        appearance = self.closet.get_current_appearance()
        self.assertEqual(appearance.fur_style, item_id)
    
    def test_statistics(self):
        """Test closet statistics."""
        stats = self.closet.get_statistics()
        
        self.assertIn('total_items', stats)
        self.assertIn('unlocked_items', stats)
        self.assertIn('by_category', stats)


class TestTranslationSystem(unittest.TestCase):
    """Test translation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TranslationManager()
    
    def test_default_language(self):
        """Test default language is English."""
        self.assertEqual(self.manager.current_language, Language.ENGLISH)
    
    def test_get_text_english(self):
        """Test getting English text."""
        text = self.manager.get_text('app_title')
        self.assertEqual(text, 'PS2 Texture Sorter')
    
    def test_get_text_with_formatting(self):
        """Test getting text with formatting."""
        text = self.manager.get_text('panda_level', level=5)
        self.assertIn('5', text)
    
    def test_set_language(self):
        """Test setting language."""
        # Create Spanish translations
        self.manager.translations[Language.SPANISH] = self.manager._get_spanish_translations()
        
        self.assertTrue(self.manager.set_language(Language.SPANISH))
        self.assertEqual(self.manager.current_language, Language.SPANISH)
        
        text = self.manager.get_text('app_title')
        self.assertEqual(text, 'Clasificador de Texturas PS2')
    
    def test_fallback_to_english(self):
        """Test fallback to English for missing translations."""
        # Set to a language with limited translations
        self.manager.current_language = Language.GERMAN
        
        # Should fall back to English
        text = self.manager.get_text('app_title')
        self.assertIsNotNone(text)
    
    def test_shorthand_function(self):
        """Test shorthand t() function."""
        text = t('app_title')
        self.assertIsNotNone(text)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMiniGameSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestPandaWidgets))
    suite.addTests(loader.loadTestsFromTestCase(TestPandaCloset))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
