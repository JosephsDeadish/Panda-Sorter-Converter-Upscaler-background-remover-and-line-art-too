# Interactive Panda Overlay System - Complete Documentation

## Overview

The Interactive Panda Overlay System provides a transparent OpenGL widget that renders a 3D panda on top of a normal Qt UI. The panda can detect, interact with, and programmatically trigger actions on Qt widgets, creating an immersive and playful user experience.

---

## Architecture

### Clean Separation of Concerns

```
┌─────────────────────────────────────────────┐
│  Transparent Panda Overlay (QOpenGLWidget)  │  ← Always on top
│  - 3D Panda rendering                       │
│  - Shadows and effects                      │
│  - Body part tracking                       │
└─────────────────────────────────────────────┘
         ↓ Detects widgets below
┌─────────────────────────────────────────────┐
│  Normal Qt UI Layer                         │
│  - QPushButton, QSlider, QTabBar            │
│  - All standard Qt widgets                  │
│  - Fully functional                         │
└─────────────────────────────────────────────┘
```

### Key Principle: NO Mixing

- ✅ UI stays in Qt Widgets
- ✅ 3D rendering only in overlay
- ✅ Clean separation maintained
- ❌ No UI in OpenGL layer
- ❌ No 3D in widget layer

---

## Components

### 1. TransparentPandaOverlay

**File**: `src/ui/transparent_panda_overlay.py`

**Purpose**: Transparent QOpenGLWidget that renders panda in 3D on top of UI.

**Key Features**:
- Full-window transparency (WA_TranslucentBackground)
- Always-on-top rendering
- Mouse event pass-through
- OpenGL 3D rendering
- Body part position tracking
- Shadow rendering
- Squash effects

**Main Methods**:
```python
# Position control
set_panda_position(x, y, z)

# Animation
set_animation_state(state)  # 'idle', 'walking', 'biting', etc.

# Effects
apply_squash_effect(factor)  # 1.0 = normal, <1.0 = squashed
set_widget_below(widget)     # For shadow rendering

# Position queries
get_head_position()    # Returns QPoint
get_mouth_position()   # Returns QPoint
get_feet_positions()   # Returns (left_foot, right_foot)
```

**Example**:
```python
overlay = TransparentPandaOverlay(main_window)
overlay.resize(main_window.size())
overlay.show()
overlay.raise_()  # Ensure on top

# Animate panda
overlay.set_animation_state('walking')
overlay.set_panda_position(1.0, -0.5, 0.0)

# Apply effects
overlay.apply_squash_effect(0.8)  # Squash when landing
```

---

### 2. WidgetDetector

**File**: `src/features/widget_detector.py`

**Purpose**: Detects Qt widgets at specific positions using hit-testing.

**Key Features**:
- Real-time widget detection
- Collision map generation
- Geometry tracking
- Distance calculations
- Widget type identification

**Main Methods**:
```python
# Detection
get_widget_at_position(x, y)        # Find widget at point
get_all_widgets()                    # Get all interactive widgets
get_nearest_widget(x, y, max_dist)  # Find closest widget

# Geometry
get_widget_center(widget)            # Returns QPoint
get_widget_rect(widget)              # Returns QRect
get_widget_bounds(widget)            # Returns (l, t, r, b)

# Collision
build_collision_map(resolution=20)   # Create obstacle grid
is_position_blocked(x, y)            # Check if occupied

# Information
get_widget_type_name(widget)         # Returns "button", "slider", etc.
get_widget_info(widget)              # Returns full info dict
```

**Example**:
```python
detector = WidgetDetector(main_window)

# Detect widget at position
widget = detector.get_widget_at_position(100, 200)
if widget:
    print(f"Found {widget.__class__.__name__}")
    center = detector.get_widget_center(widget)
    print(f"Center: {center.x()}, {center.y()}")

# Build collision map for path finding
collision_map = detector.build_collision_map(resolution=20)

# Find nearest widget to panda
widget, distance = detector.get_nearest_widget(panda_x, panda_y)
```

---

### 3. PandaInteractionBehavior

**File**: `src/features/panda_interaction_behavior.py`

**Purpose**: AI system for autonomous widget interaction.

**Key Features**:
- Autonomous decision making
- Widget-specific behaviors
- Animation coordination
- Programmatic clicking
- Personality parameters

**Behavior Types**:
- `BITE_BUTTON` - Chomp and click button
- `JUMP_ON_BUTTON` - Bounce and click button
- `TAP_SLIDER` - Tap and change slider value
- `BITE_TAB` - Bite and switch tab
- `PUSH_CHECKBOX` - Push and toggle checkbox
- `SPIN_COMBOBOX` - Spin and open dropdown
- `MISCHIEVOUS_LOOK` - Just stare at widget
- `WALK_AROUND` - Navigate around obstacles

**Main Methods**:
```python
# Update (call every frame)
update(delta_time)  # Updates AI, animations, interactions

# Manual control
force_interact_with_widget(widget, behavior=None)

# Personality
set_mischievousness(level)  # 0.0-1.0, interaction frequency
set_playfulness(level)       # 0.0-1.0, animation exaggeration
```

**Example**:
```python
behavior = PandaInteractionBehavior(overlay, detector)

# Configure personality
behavior.set_mischievousness(0.8)  # Very mischievous
behavior.set_playfulness(0.9)       # Very playful

# Update every frame
def update_loop():
    behavior.update(0.016)  # 60 FPS
    QTimer.singleShot(16, update_loop)

update_loop()

# Force interaction
button = QPushButton("Click me!")
behavior.force_interact_with_widget(button)
```

---

## Integration Guide

### Step 1: Setup Main Window

```python
from PyQt6.QtWidgets import QMainWindow
from src.ui.transparent_panda_overlay import TransparentPandaOverlay
from src.features.widget_detector import WidgetDetector
from src.features.panda_interaction_behavior import PandaInteractionBehavior

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_panda_overlay()
    
    def setup_ui(self):
        # Create your normal UI
        # Tabs, buttons, sliders, etc.
        pass
    
    def setup_panda_overlay(self):
        # Create overlay
        self.overlay = TransparentPandaOverlay(self)
        self.overlay.resize(self.size())
        self.overlay.show()
        self.overlay.raise_()
        
        # Setup detector
        self.detector = WidgetDetector(self)
        
        # Setup behavior
        self.behavior = PandaInteractionBehavior(
            self.overlay,
            self.detector
        )
        self.behavior.set_mischievousness(0.7)
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_panda)
        self.timer.start(16)  # 60 FPS
    
    def update_panda(self):
        # Update AI
        self.behavior.update(0.016)
        
        # Update shadow based on widget below
        head_pos = self.overlay.get_head_position()
        if head_pos:
            widget = self.detector.get_widget_at_position(
                head_pos.x(), head_pos.y()
            )
            self.overlay.set_widget_below(widget)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())
        self.detector.invalidate_cache()
```

### Step 2: Handle Events

Widgets work normally! No special handling needed. The panda overlay:
- Passes mouse events through when not on panda
- Programmatically triggers widget actions
- Widget callbacks fire as usual

### Step 3: Customize Behavior (Optional)

```python
# Make panda more/less mischievous
behavior.set_mischievousness(0.5)  # Less frequent interactions

# Make panda more/less playful
behavior.set_playfulness(0.7)  # Moderate animation

# Change detection radius
behavior.detection_radius = 300  # Pixels

# Change cooldown between interactions
behavior.interaction_cooldown_max = 8.0  # Seconds
```

---

## Interaction Flow

### Example: Button Bite

```
1. Panda AI update detects nearby button
   ↓
2. Chooses BITE_BUTTON behavior
   ↓
3. Panda walks toward button
   ↓
4. Animation: Mouth opens wide
   ↓
5. Animation: Chomps down
   ↓
6. Wait 500ms (QTimer.singleShot)
   ↓
7. button.click() triggered programmatically
   ↓
8. Visual: Shadow darkens
   ↓
9. Visual: Squash effect (factor 0.8)
   ↓
10. Button's clicked signal fires
   ↓
11. Your callback executes
   ↓
12. Squash releases (factor 1.0)
   ↓
13. Panda returns to idle state
   ↓
14. Cooldown timer starts (5+ seconds)
```

### Example: Slider Tap

```
1. Panda detects slider
   ↓
2. Chooses TAP_SLIDER behavior
   ↓
3. Panda positions above slider
   ↓
4. Animation: Jumps up
   ↓
5. Animation: Falls down
   ↓
6. Wait 400ms
   ↓
7. slider.setValue(random_value) triggered
   ↓
8. Visual: Squash effect on landing
   ↓
9. Slider's valueChanged signal fires
   ↓
10. Your callback executes
   ↓
11. Panda bounces back
   ↓
12. Returns to idle
```

---

## Visual Effects

### Shadow Rendering

Shadows are rendered dynamically under the panda:
- Elliptical shadow shape
- Opacity based on height
- Rendered onto widget below
- OpenGL blend mode

### Squash Effects

Squash factor creates depth illusion:
- `1.0` = Normal height
- `<1.0` = Squashed (pressing down)
- `>1.0` = Stretched (jumping up)
- Smooth transitions via lerp

---

## Performance

### Optimization Techniques

1. **60 FPS Rendering**: Overlay updates at 60 FPS via QTimer
2. **Widget Caching**: Detector caches widget list
3. **Collision Grid**: Grid-based collision map (configurable resolution)
4. **Lazy Updates**: Only update when needed
5. **Hardware Acceleration**: OpenGL for 3D rendering

### Typical Performance

- **CPU Usage**: ~5-10% on moderate hardware
- **GPU Usage**: ~10-20% (OpenGL rendering)
- **Memory**: ~50MB additional (for overlay + detector)
- **Frame Time**: 1-3ms per frame

---

## Troubleshooting

### Overlay Not Visible

Check:
- `overlay.show()` called
- `overlay.raise_()` called
- PyQt6 and OpenGL installed
- Window size matches: `overlay.resize(main_window.size())`

### Mouse Events Not Passing Through

Check:
- `WA_TransparentForMouseEvents` not set to True when it should be False
- Mouse event handling in `mousePressEvent`
- Click detection logic

### Panda Not Interacting

Check:
- `behavior.update()` called every frame
- Cooldown not preventing interaction (check `interaction_cooldown`)
- Mischievousness level not too low
- Widgets are visible and enabled

### Widget Not Detected

Check:
- Widget is in `detector.interactive_types` tuple
- Widget is visible (`widget.isVisible()`)
- Widget is enabled (`widget.isEnabled()`)
- Cache is valid (`detector.invalidate_cache()` after UI changes)

---

## Testing

### Run Test Suite

```bash
python test_interactive_overlay.py
```

Tests:
- Module imports
- PyQt6/OpenGL availability
- Class structure
- Method existence
- Behavior enums

### Run Integration Example

```bash
python test_integration_example.py
```

Creates demo window with:
- Tabs
- Buttons
- Sliders
- Checkboxes
- Comboboxes
- Interactive panda overlay

---

## API Reference

### TransparentPandaOverlay

**Signals**:
- `panda_moved(int, int)` - Emitted when panda moves
- `panda_clicked_widget(object)` - Emitted when panda clicks widget

**Properties**:
- `panda_x`, `panda_y`, `panda_z` - 3D position
- `panda_rotation` - Y-axis rotation
- `animation_state` - Current animation
- `squash_factor` - Squash effect (0.5-1.5)

### WidgetDetector

**Properties**:
- `interactive_types` - Tuple of widget types to detect
- `collision_map` - Dict of grid positions to widgets
- `cached_widgets` - List of detected widgets

### PandaInteractionBehavior

**Properties**:
- `mischievousness` - Interaction frequency (0.0-1.0)
- `playfulness` - Animation exaggeration (0.0-1.0)
- `detection_radius` - Detection range in pixels
- `interaction_cooldown_max` - Cooldown duration in seconds

---

## Advanced Usage

### Custom Behaviors

Add custom interaction behaviors:

```python
# In panda_interaction_behavior.py
class InteractionBehavior(Enum):
    # ... existing behaviors ...
    CUSTOM_DANCE = "custom_dance"

# In PandaInteractionBehavior class
def _execute_interaction(self):
    # ... existing code ...
    elif behavior == InteractionBehavior.CUSTOM_DANCE:
        self._animate_dance()
        self.behavior_duration = 2.0

def _animate_dance(self):
    print("Panda dancing!")
    self.overlay.set_animation_state('dancing')
```

### Custom Widget Types

Detect custom widgets:

```python
from myapp import MyCustomWidget

detector = WidgetDetector(main_window)
detector.interactive_types = detector.interactive_types + (MyCustomWidget,)
```

### Path Finding

Use collision map for path finding:

```python
collision_map = detector.build_collision_map(resolution=20)

def is_path_clear(from_x, from_y, to_x, to_y):
    # Simple line-of-sight check
    # (Real implementation would use A* or similar)
    steps = 10
    for i in range(steps):
        t = i / steps
        x = from_x + (to_x - from_x) * t
        y = from_y + (to_y - from_y) * t
        
        if detector.is_position_blocked(x, y):
            return False
    return True
```

---

## Best Practices

1. **Always call `overlay.raise_()`** after showing to ensure it's on top
2. **Update overlay size on resize** via `resizeEvent`
3. **Invalidate detector cache** when UI changes significantly
4. **Use reasonable cooldowns** to prevent overwhelming users
5. **Test with various widget types** to ensure compatibility
6. **Monitor performance** on target hardware
7. **Provide user control** over panda behavior (enable/disable, personality)

---

## Future Enhancements

Possible additions:
- [ ] Path finding with A* algorithm
- [ ] Multiple pandas
- [ ] Panda-to-panda interaction
- [ ] Speech bubbles
- [ ] More animation states
- [ ] Particle effects
- [ ] Sound effects
- [ ] User training mode (panda shows how to use UI)
- [ ] Accessibility features (panda guides navigation)

---

## Credits

Interactive Panda Overlay System
- Design: Clean architecture with separation of UI and 3D
- Implementation: PyQt6 + OpenGL
- License: Part of PS2-texture-sorter project

---

## Support

For issues, questions, or contributions:
- Check test suite: `python test_interactive_overlay.py`
- Run integration example: `python test_integration_example.py`
- Review this documentation
- Check source code comments

---

**Interactive Panda Overlay System - Making UIs Fun!** 🐼✨
