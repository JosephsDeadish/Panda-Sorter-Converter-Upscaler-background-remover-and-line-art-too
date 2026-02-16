"""
Test suite for OpenGL Panda Widget
Tests hardware-accelerated 3D rendering, lighting, shadows, and physics
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def test_imports():
    """Test that OpenGL widget can be imported."""
    try:
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        print("✅ OpenGL widget imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import OpenGL widget: {e}")
        print("   Install dependencies: pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
        return False

def test_qt_available():
    """Test that Qt is available."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtOpenGL import QOpenGLWidget
        print("✅ PyQt6 is available")
        return True
    except ImportError:
        print("❌ PyQt6 not available")
        print("   Install: pip install PyQt6")
        return False

def test_opengl_available():
    """Test that OpenGL is available."""
    try:
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
        print("✅ PyOpenGL is available")
        return True
    except ImportError:
        print("❌ PyOpenGL not available")
        print("   Install: pip install PyOpenGL PyOpenGL-accelerate")
        return False

def test_widget_creation():
    """Test creating OpenGL widget."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        # Create Qt application (needed for widgets)
        if not QApplication.instance():
            app = QApplication([])
        
        # Create panda character
        panda = PandaCharacter("TestPanda")
        
        # Create OpenGL widget
        widget = PandaOpenGLWidget(panda)
        
        # Check basic properties
        assert hasattr(widget, 'panda')
        assert hasattr(widget, 'animation_frame')
        assert hasattr(widget, 'animation_state')
        assert widget.TARGET_FPS == 60
        assert widget.FRAME_TIME == 1.0 / 60.0
        
        print("✅ Widget creation successful")
        print(f"   - Animation state: {widget.animation_state}")
        print(f"   - FPS target: {widget.TARGET_FPS}")
        print(f"   - Camera distance: {widget.camera_distance}")
        
        return True
    except Exception as e:
        print(f"❌ Widget creation failed: {e}")
        return False

def test_3d_constants():
    """Test 3D dimension constants."""
    try:
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        
        # Check panda dimensions
        assert PandaOpenGLWidget.HEAD_RADIUS > 0
        assert PandaOpenGLWidget.BODY_WIDTH > 0
        assert PandaOpenGLWidget.BODY_HEIGHT > 0
        assert PandaOpenGLWidget.ARM_LENGTH > 0
        assert PandaOpenGLWidget.LEG_LENGTH > 0
        assert PandaOpenGLWidget.EAR_SIZE > 0
        
        print("✅ 3D constants defined correctly")
        print(f"   - Head radius: {PandaOpenGLWidget.HEAD_RADIUS}")
        print(f"   - Body size: {PandaOpenGLWidget.BODY_WIDTH}x{PandaOpenGLWidget.BODY_HEIGHT}")
        print(f"   - Limb lengths: arms={PandaOpenGLWidget.ARM_LENGTH}, legs={PandaOpenGLWidget.LEG_LENGTH}")
        
        return True
    except Exception as e:
        print(f"❌ 3D constants test failed: {e}")
        return False

def test_physics_constants():
    """Test physics constants."""
    try:
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        
        # Check physics
        assert PandaOpenGLWidget.GRAVITY > 0
        assert 0 < PandaOpenGLWidget.BOUNCE_DAMPING < 1
        assert 0 < PandaOpenGLWidget.FRICTION < 1
        
        print("✅ Physics constants defined correctly")
        print(f"   - Gravity: {PandaOpenGLWidget.GRAVITY}")
        print(f"   - Bounce damping: {PandaOpenGLWidget.BOUNCE_DAMPING}")
        print(f"   - Friction: {PandaOpenGLWidget.FRICTION}")
        
        return True
    except Exception as e:
        print(f"❌ Physics constants test failed: {e}")
        return False

def test_lighting_system():
    """Test lighting system."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        if not QApplication.instance():
            app = QApplication([])
        
        panda = PandaCharacter("TestPanda")
        widget = PandaOpenGLWidget(panda)
        
        # Check lighting properties
        assert hasattr(widget, 'light_position')
        assert hasattr(widget, 'ambient_light')
        assert hasattr(widget, 'diffuse_light')
        assert hasattr(widget, 'specular_light')
        
        assert len(widget.light_position) == 4
        assert len(widget.ambient_light) == 4
        assert len(widget.diffuse_light) == 4
        assert len(widget.specular_light) == 4
        
        print("✅ Lighting system configured")
        print(f"   - Light position: {widget.light_position[:3]}")
        print(f"   - Ambient: {widget.ambient_light[:3]}")
        print(f"   - Diffuse: {widget.diffuse_light[:3]}")
        
        return True
    except Exception as e:
        print(f"❌ Lighting system test failed: {e}")
        return False

def test_shadow_mapping():
    """Test shadow mapping system."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        if not QApplication.instance():
            app = QApplication([])
        
        panda = PandaCharacter("TestPanda")
        widget = PandaOpenGLWidget(panda)
        
        # Check shadow properties
        assert hasattr(widget, 'shadow_map_size')
        assert widget.shadow_map_size > 0
        assert hasattr(widget, 'shadow_fbo')
        assert hasattr(widget, 'shadow_texture')
        
        print("✅ Shadow mapping system configured")
        print(f"   - Shadow map size: {widget.shadow_map_size}x{widget.shadow_map_size}")
        
        return True
    except Exception as e:
        print(f"❌ Shadow mapping test failed: {e}")
        return False

def test_animation_states():
    """Test animation state management."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        if not QApplication.instance():
            app = QApplication([])
        
        panda = PandaCharacter("TestPanda")
        widget = PandaOpenGLWidget(panda)
        
        # Test setting animation states
        test_states = ['idle', 'walking', 'jumping', 'waving', 'celebrating']
        
        for state in test_states:
            widget.set_animation_state(state)
            assert widget.animation_state == state
        
        print("✅ Animation states work correctly")
        print(f"   - Tested states: {', '.join(test_states)}")
        
        return True
    except Exception as e:
        print(f"❌ Animation states test failed: {e}")
        return False

def test_3d_items():
    """Test 3D item system."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        if not QApplication.instance():
            app = QApplication([])
        
        panda = PandaCharacter("TestPanda")
        widget = PandaOpenGLWidget(panda)
        
        # Add items
        widget.add_item_3d('food', x=0.5, y=0.0, z=0.0, color=[1.0, 0.0, 0.0])
        widget.add_item_3d('toy', x=-0.5, y=0.0, z=0.0, color=[0.0, 0.0, 1.0])
        
        assert len(widget.items_3d) == 2
        assert widget.items_3d[0]['type'] == 'food'
        assert widget.items_3d[1]['type'] == 'toy'
        
        # Test clearing
        widget.clear_items()
        assert len(widget.items_3d) == 0
        
        print("✅ 3D items system working")
        print(f"   - Can add food items")
        print(f"   - Can add toy items")
        print(f"   - Can clear items")
        
        return True
    except Exception as e:
        print(f"❌ 3D items test failed: {e}")
        return False

def test_camera_system():
    """Test camera system."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.panda_widget_gl import PandaOpenGLWidget
        from src.features.panda_character import PandaCharacter
        
        if not QApplication.instance():
            app = QApplication([])
        
        panda = PandaCharacter("TestPanda")
        widget = PandaOpenGLWidget(panda)
        
        # Check camera properties
        assert hasattr(widget, 'camera_distance')
        assert hasattr(widget, 'camera_angle_x')
        assert hasattr(widget, 'camera_angle_y')
        
        # Test camera distance bounds
        initial_distance = widget.camera_distance
        assert 1.0 <= initial_distance <= 10.0
        
        print("✅ Camera system configured")
        print(f"   - Distance: {widget.camera_distance}")
        print(f"   - Angle X: {widget.camera_angle_x}°")
        print(f"   - Angle Y: {widget.camera_angle_y}°")
        
        return True
    except Exception as e:
        print(f"❌ Camera system test failed: {e}")
        return False

def test_deprecation_warning():
    """Test that old canvas widget shows deprecation warning."""
    try:
        import warnings
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import old canvas widget (should trigger warning)
            from src.ui import panda_widget
            
            # Check if deprecation warning was raised
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            
            print("✅ Deprecation warning working")
            print(f"   - Old canvas widget shows warning")
            print(f"   - Warning: {w[0].message}")
            
            return True
    except Exception as e:
        print(f"❌ Deprecation warning test failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("OpenGL Panda Widget Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Qt Available", test_qt_available),
        ("OpenGL Available", test_opengl_available),
        ("Imports", test_imports),
        ("Widget Creation", test_widget_creation),
        ("3D Constants", test_3d_constants),
        ("Physics Constants", test_physics_constants),
        ("Lighting System", test_lighting_system),
        ("Shadow Mapping", test_shadow_mapping),
        ("Animation States", test_animation_states),
        ("3D Items", test_3d_items),
        ("Camera System", test_camera_system),
        ("Deprecation Warning", test_deprecation_warning),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print()
        print("🎉 All tests passed! OpenGL panda widget is ready!")
        print()
        print("Next steps:")
        print("  1. Run the application with: python main.py")
        print("  2. The OpenGL panda should appear in a separate window")
        print("  3. Try clicking, dragging, and zooming the panda")
        print("  4. Enjoy hardware-accelerated 3D rendering!")
    else:
        print()
        print("⚠️  Some tests failed. Check dependencies:")
        print("  pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
