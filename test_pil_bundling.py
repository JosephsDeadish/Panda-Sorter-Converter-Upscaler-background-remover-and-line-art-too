#!/usr/bin/env python3
"""
Test PIL Bundling and Vision Model Hooks
Validates that PyInstaller hooks correctly bundle PIL and vision models

This test verifies:
1. hook-PIL.py collects all necessary PIL modules and data
2. hook-vision_models.py collects vision model dependencies
3. build_spec_onefolder.spec correctly references hooks
4. PIL._imaging binary module is included
5. PIL plugins are included
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestPILHook(unittest.TestCase):
    """Test PIL PyInstaller hook."""
    
    def setUp(self):
        """Set up test environment."""
        self.hook_path = project_root / '.github' / 'hooks' / 'hook-PIL.py'
    
    def test_pil_hook_exists(self):
        """Test that hook-PIL.py exists."""
        self.assertTrue(self.hook_path.exists(), "hook-PIL.py should exist")
    
    def test_pil_hook_has_binary_modules(self):
        """Test that hook includes PIL binary modules."""
        with open(self.hook_path, 'r') as f:
            content = f.read()
        
        # Check for critical binary modules
        self.assertIn("PIL._imaging", content, "Should include PIL._imaging binary module")
        self.assertIn("hiddenimports", content, "Should define hiddenimports")
    
    def test_pil_hook_has_plugins(self):
        """Test that hook includes PIL image format plugins."""
        with open(self.hook_path, 'r') as f:
            content = f.read()
        
        # Check for image format plugins
        plugins = [
            "PngImagePlugin",
            "JpegImagePlugin",
            "TiffImagePlugin",
            "BmpImagePlugin",
        ]
        
        for plugin in plugins:
            self.assertIn(plugin, content, f"Should include {plugin}")
    
    def test_pil_hook_collects_data(self):
        """Test that hook collects PIL data files."""
        with open(self.hook_path, 'r') as f:
            content = f.read()
        
        self.assertIn("collect_data_files", content, "Should use collect_data_files")
        self.assertIn("include_py_files=True", content, "Should include Python files")
        self.assertIn("datas", content, "Should define datas")


class TestVisionModelHooks(unittest.TestCase):
    """Test vision model PyInstaller hooks."""
    
    def setUp(self):
        """Set up test environment."""
        self.hooks_dir = project_root / '.github' / 'hooks'
    
    def test_clip_hook_exists(self):
        """Test that hook-clip_model.py exists."""
        hook_path = self.hooks_dir / 'hook-clip_model.py'
        self.assertTrue(hook_path.exists(), "hook-clip_model.py should exist")
    
    def test_dinov2_hook_exists(self):
        """Test that hook-dinov2_model.py exists."""
        hook_path = self.hooks_dir / 'hook-dinov2_model.py'
        self.assertTrue(hook_path.exists(), "hook-dinov2_model.py should exist")
    
    def test_vision_models_hook_exists(self):
        """Test that hook-vision_models.py exists."""
        hook_path = self.hooks_dir / 'hook-vision_models.py'
        self.assertTrue(hook_path.exists(), "hook-vision_models.py should exist")
    
    def test_clip_hook_includes_pil(self):
        """Test that CLIP hook includes PIL dependencies."""
        hook_path = self.hooks_dir / 'hook-clip_model.py'
        with open(hook_path, 'r') as f:
            content = f.read()
        
        self.assertIn("PIL", content, "CLIP hook should include PIL")
        self.assertIn("PIL._imaging", content, "CLIP hook should include PIL._imaging")
    
    def test_clip_hook_includes_torch(self):
        """Test that CLIP hook includes PyTorch dependencies."""
        hook_path = self.hooks_dir / 'hook-clip_model.py'
        with open(hook_path, 'r') as f:
            content = f.read()
        
        self.assertIn("torch", content, "CLIP hook should include torch")
        self.assertIn("transformers", content, "CLIP hook should include transformers")
    
    def test_dinov2_hook_includes_pil(self):
        """Test that DINOv2 hook includes PIL dependencies."""
        hook_path = self.hooks_dir / 'hook-dinov2_model.py'
        with open(hook_path, 'r') as f:
            content = f.read()
        
        self.assertIn("PIL", content, "DINOv2 hook should include PIL")
        self.assertIn("PIL._imaging", content, "DINOv2 hook should include PIL._imaging")
    
    def test_vision_models_hook_includes_all_deps(self):
        """Test that vision_models hook includes all dependencies."""
        hook_path = self.hooks_dir / 'hook-vision_models.py'
        with open(hook_path, 'r') as f:
            content = f.read()
        
        deps = ["PIL", "torch", "transformers", "timm", "open_clip"]
        for dep in deps:
            self.assertIn(dep, content, f"vision_models hook should include {dep}")


class TestBuildSpec(unittest.TestCase):
    """Test build spec configuration."""
    
    def setUp(self):
        """Set up test environment."""
        self.spec_path = project_root / 'build_spec_onefolder.spec'
    
    def test_build_spec_exists(self):
        """Test that build spec exists."""
        self.assertTrue(self.spec_path.exists(), "build_spec_onefolder.spec should exist")
    
    def test_build_spec_has_pil_collection(self):
        """Test that build spec explicitly collects PIL."""
        with open(self.spec_path, 'r') as f:
            content = f.read()
        
        self.assertIn("PIL_DATA", content, "Build spec should define PIL_DATA")
        self.assertIn("import PIL", content, "Build spec should import PIL to get path")
    
    def test_build_spec_has_torch_collection(self):
        """Test that build spec explicitly collects torch."""
        with open(self.spec_path, 'r') as f:
            content = f.read()
        
        self.assertIn("TORCH_DATA", content, "Build spec should define TORCH_DATA")
        self.assertIn("import torch", content, "Build spec should import torch to get path")
    
    def test_build_spec_has_hookspath_validation(self):
        """Test that build spec validates hookspath."""
        with open(self.spec_path, 'r') as f:
            content = f.read()
        
        self.assertIn("HOOKSPATH", content, "Build spec should define HOOKSPATH")
        self.assertIn(".github/hooks", content, "Build spec should include .github/hooks in hookspath")
    
    def test_build_spec_includes_pil_in_datas(self):
        """Test that build spec adds PIL to datas."""
        with open(self.spec_path, 'r') as f:
            content = f.read()
        
        # Check that PIL_DATA is added to datas
        self.assertIn("PIL_DATA", content, "Build spec should use PIL_DATA")
        # The conditional addition pattern
        self.assertIn("[PIL_DATA] if PIL_DATA", content, "Build spec should conditionally add PIL_DATA")


class TestMainDiagnostics(unittest.TestCase):
    """Test main.py diagnostics."""
    
    def setUp(self):
        """Set up test environment."""
        self.main_path = project_root / 'main.py'
    
    def test_main_has_pil_check(self):
        """Test that main.py checks for PIL."""
        with open(self.main_path, 'r') as f:
            content = f.read()
        
        self.assertIn("'pil'", content, "main.py should check for PIL")
        self.assertIn("from PIL import Image", content, "main.py should import PIL")
    
    def test_main_checks_pil_binary_module(self):
        """Test that main.py checks PIL._imaging."""
        with open(self.main_path, 'r') as f:
            content = f.read()
        
        self.assertIn("PIL._imaging", content, "main.py should check PIL._imaging binary module")
    
    def test_main_requires_pil_for_vision_models(self):
        """Test that main.py requires PIL for vision models."""
        with open(self.main_path, 'r') as f:
            content = f.read()
        
        # CLIP should require PIL
        self.assertIn("features['pil'] and features['pytorch']", content, 
                      "Vision models should require PIL")


class TestOrganizerPanel(unittest.TestCase):
    """Test organizer panel PIL handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.panel_path = project_root / 'src' / 'ui' / 'organizer_panel_qt.py'
    
    def test_organizer_has_pil_check(self):
        """Test that organizer panel checks for PIL."""
        with open(self.panel_path, 'r') as f:
            content = f.read()
        
        self.assertIn("PIL_AVAILABLE", content, "Organizer should have PIL_AVAILABLE flag")
        self.assertIn("from PIL import Image", content, "Organizer should import PIL")
    
    def test_organizer_has_graceful_fallback(self):
        """Test that organizer panel has graceful fallback for missing PIL."""
        with open(self.panel_path, 'r') as f:
            content = f.read()
        
        # Check for error handling
        self.assertIn("except ImportError", content, "Should handle ImportError for PIL")
        self.assertIn("except Exception", content, "Should handle general exceptions")
    
    def test_organizer_mentions_pil_in_errors(self):
        """Test that error messages mention PIL."""
        with open(self.panel_path, 'r') as f:
            content = f.read()
        
        # Should mention PIL/pillow in error messages
        self.assertIn("PIL", content, "Error messages should mention PIL")
        self.assertIn("pillow", content.lower(), "Error messages should mention pillow")


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPILHook))
    suite.addTests(loader.loadTestsFromTestCase(TestVisionModelHooks))
    suite.addTests(loader.loadTestsFromTestCase(TestBuildSpec))
    suite.addTests(loader.loadTestsFromTestCase(TestMainDiagnostics))
    suite.addTests(loader.loadTestsFromTestCase(TestOrganizerPanel))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
