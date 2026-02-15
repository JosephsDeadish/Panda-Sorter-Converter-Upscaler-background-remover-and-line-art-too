# Qt + OpenGL Architecture

## Overview
This application uses a clean separation of concerns between Qt and OpenGL:

## Qt Responsibilities
- **UI Controls**: Buttons, tabs, sliders, text inputs, checkboxes
- **Layout Management**: QVBoxLayout, QHBoxLayout, QGridLayout
- **Event Handling**: Mouse clicks, keyboard input, widget interactions
- **Animation State Control**: QTimer for managing animation state updates
- **Signals/Slots**: Communication between components

## OpenGL Responsibilities  
- **3D Rendering**: All hardware-accelerated 3D graphics
- **Panda Character Rendering**: Skeletal animations, limbs, clothing
- **Real-time Effects**: Lighting, shadows, physics simulations
- **60 FPS Rendering**: Smooth frame updates via paintGL()

## Panda Widget Architecture (`panda_widget_gl.py`)

### Correct Pattern ✓
```python
class PandaOpenGLWidget(QOpenGLWidget):
    """
    - Qt provides: Widget container, QTimer for state updates
    - OpenGL provides: All rendering via initializeGL/paintGL/resizeGL
    """
    
    def __init__(self):
        super().__init__()
        # QTimer ONLY updates animation state, not rendering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(16)  # 60 FPS state updates
    
    def _update_animation(self):
        """Update animation STATE only - no rendering here"""
        self.rotation += self.rotation_speed
        self.bounce_phase += 0.1
        self.update()  # Triggers paintGL()
    
    def paintGL(self):
        """OpenGL does ALL rendering here"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # ... OpenGL rendering code ...
```

### What NOT to Do ✗
```python
# DON'T: Mix canvas/tkinter rendering with OpenGL
# DON'T: Use QTimer.timeout to directly render (use it to trigger update())
# DON'T: Use tkinter .after() in Qt widgets
# DON'T: Mix Qt widgets inside OpenGL rendering context
```

## File Organization

### OpenGL Files
- `src/ui/panda_widget_gl.py` - Main OpenGL panda widget
- `src/ui/transparent_panda_overlay.py` - Transparent overlay rendering

### Qt UI Files
- `src/ui/*_qt.py` - Pure Qt UI panels
- `src/ui/qt_panel_loader.py` - Dynamic Qt/Tkinter panel loading
- `src/ui/performance_utils_qt.py` - Qt timer utilities

### Migration Status
- ✓ Panda rendering: Fully OpenGL
- ✓ UI controls: Pure Qt (PyQt6)
- ✓ Timing: QTimer for state, paintGL() for rendering
- ✓ No canvas usage in new code
- ✓ No .after() in Qt widgets

## Key Principles

1. **Separation of Concerns**: Qt handles UI, OpenGL handles rendering
2. **State vs Rendering**: QTimer updates state, paintGL() renders
3. **No Mixing**: Don't mix tkinter with Qt, or canvas with OpenGL
4. **Performance**: OpenGL provides hardware acceleration for smooth 60 FPS
5. **Clean APIs**: Signals/slots for communication, not direct calls

## Example: Animation Loop

```python
# STATE UPDATE (Qt Timer - 60 FPS)
def _update_animation(self):
    self.panda_state.update(dt=0.016)  # Update physics, positions
    self.update()  # Schedule repaint

# RENDERING (OpenGL)
def paintGL(self):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    self._render_panda(self.panda_state)  # Use state to render
```

This architecture ensures smooth performance and maintainable code.
