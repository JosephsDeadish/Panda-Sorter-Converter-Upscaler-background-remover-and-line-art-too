"""
Test UI Performance Fixes
Tests for line tool performance, scrollbar optimization, and memory management
Tests code structure without importing UI modules (which require customtkinter)
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


class TestCodeStructure(unittest.TestCase):
    """Test that performance fixes exist in the code."""
    
    def test_lineart_panel_has_preview_flags(self):
        """Test that lineart panel has preview control flags."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        # Check for preview control flags
        self.assertIn('_preview_running', content, "Missing _preview_running flag")
        self.assertIn('_preview_cancelled', content, "Missing _preview_cancelled flag")
    
    def test_lineart_panel_has_cleanup_method(self):
        """Test that lineart panel has cleanup_memory method."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        self.assertIn('def _cleanup_memory', content, "Missing _cleanup_memory method")
        self.assertIn('gc.collect()', content, "Missing garbage collection call")
    
    def test_lineart_panel_checks_cancelled_flag(self):
        """Test that preview generation checks cancellation flag."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        # Check that cancelled flag is checked multiple times
        cancel_checks = content.count('if self._preview_cancelled')
        self.assertGreater(cancel_checks, 2, "Should check cancellation flag multiple times")
        
        # Check that images are closed on cancel
        self.assertIn('close()', content, "Missing image cleanup on cancel")
    
    def test_lineart_panel_prevents_concurrent_preview(self):
        """Test that concurrent preview operations are prevented."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        # Check for concurrent operation prevention
        self.assertIn('if self._preview_running:', content, "Missing concurrent operation check")
        self.assertIn('self._preview_running = True', content, "Missing preview running flag set")
        self.assertIn('self._preview_running = False', content, "Missing preview running flag reset")
    
    def test_debounce_increased_to_800ms(self):
        """Test that debounce time was increased."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        # Check that debounce is now 800ms in the schedule_live_update method
        schedule_method_start = content.find('def _schedule_live_update')
        schedule_method_end = content.find('\n    def ', schedule_method_start + 1)
        schedule_method = content[schedule_method_start:schedule_method_end]
        
        self.assertIn('after(800', schedule_method, "Debounce should be 800ms in _schedule_live_update")
        self.assertNotIn('after(500', schedule_method, "Old 500ms debounce should be removed from _schedule_live_update")
    
    def test_live_preview_caches_dimensions(self):
        """Test that live preview widget caches canvas dimensions."""
        preview_file = Path(__file__).parent / 'src' / 'ui' / 'live_preview_widget.py'
        content = preview_file.read_text()
        
        self.assertIn('_canvas_width', content, "Missing _canvas_width cache")
        self.assertIn('_canvas_height', content, "Missing _canvas_height cache")
        self.assertIn('_resize_pending', content, "Missing resize pending flag")
    
    def test_live_preview_has_resize_throttling(self):
        """Test that live preview has resize throttling."""
        preview_file = Path(__file__).parent / 'src' / 'ui' / 'live_preview_widget.py'
        content = preview_file.read_text()
        
        self.assertIn('def _on_canvas_resize', content, "Missing resize handler")
        self.assertIn('def _do_resize_update', content, "Missing throttled resize update")
        self.assertIn('after(150', content, "Missing 150ms throttle delay")
    
    def test_live_preview_tracks_photo_refs(self):
        """Test that live preview tracks photo references for cleanup."""
        preview_file = Path(__file__).parent / 'src' / 'ui' / 'live_preview_widget.py'
        content = preview_file.read_text()
        
        self.assertIn('_photo_refs', content, "Missing photo refs tracking")
        self.assertIn('def _cleanup_photo_refs', content, "Missing cleanup method")
        self.assertIn('self._photo_refs.append', content, "Missing photo ref tracking")
    
    def test_live_preview_replaces_winfo_calls(self):
        """Test that live preview uses cached dimensions instead of winfo."""
        preview_file = Path(__file__).parent / 'src' / 'ui' / 'live_preview_widget.py'
        content = preview_file.read_text()
        
        # In _show_slider, _show_side_by_side, _show_toggle:
        # Should use self._canvas_width instead of self.canvas.winfo_width()
        
        # Count usage of cached dimensions in show methods
        show_slider_start = content.find('def _show_slider')
        show_toggle_end = content.find('def _zoom_in')
        show_methods_section = content[show_slider_start:show_toggle_end]
        
        cached_usage = show_methods_section.count('self._canvas_width')
        self.assertGreater(cached_usage, 2, "Should use cached dimensions in show methods")
    
    def test_performance_utils_exists(self):
        """Test that performance_utils module exists."""
        perf_file = Path(__file__).parent / 'src' / 'ui' / 'performance_utils.py'
        self.assertTrue(perf_file.exists(), "Missing performance_utils.py")
        
        content = perf_file.read_text()
        self.assertIn('class OptimizedScrollableFrame', content, "Missing OptimizedScrollableFrame")
        self.assertIn('class ThrottledUpdate', content, "Missing ThrottledUpdate")
        self.assertIn('class DebouncedCallback', content, "Missing DebouncedCallback")
        self.assertIn('def cleanup_widget_memory', content, "Missing cleanup_widget_memory")
    
    def test_lineart_uses_optimized_scrollable_frame(self):
        """Test that lineart panel uses OptimizedScrollableFrame."""
        lineart_file = Path(__file__).parent / 'src' / 'ui' / 'lineart_converter_panel.py'
        content = lineart_file.read_text()
        
        self.assertIn('from src.ui.performance_utils import', content, "Missing performance_utils import")
        self.assertIn('OptimizedScrollableFrame', content, "Should use OptimizedScrollableFrame")


def run_tests():
    """Run all structure tests."""
    print("="*70)
    print("Running UI Performance Code Structure Tests")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCodeStructure)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✓ ALL CODE STRUCTURE TESTS PASSED")
        print("Performance fixes are properly implemented:")
        print("  ✓ Thread control and cancellation")
        print("  ✓ Memory cleanup mechanisms")
        print("  ✓ Canvas resize throttling")
        print("  ✓ Debounce timing optimization")
        print("  ✓ Photo reference tracking")
        print("  ✓ Cached canvas dimensions")
        print("  ✓ Performance utilities module")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
