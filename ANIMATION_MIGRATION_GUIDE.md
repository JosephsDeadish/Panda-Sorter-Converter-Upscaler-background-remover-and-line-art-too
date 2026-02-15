# Tkinter to Qt Animation/Timing Migration Guide

## Overview

This guide documents the replacement of tkinter's `.after()` timing system with Qt's native animation and timing system (QTimer, QPropertyAnimation, QParallelAnimationGroup, QStateMachine).

## Why Replace Tkinter Animation/Timing?

### Problems with Tkinter `.after()`:
1. **Not integrated** with Qt event loop → conflicts and overhead
2. **Manual ID tracking** required for cancellation
3. **Recursive calls** can cause stack issues
4. **No easing curves** - linear only
5. **Mixing frameworks** causes performance issues

### Benefits of Qt Native Animation:
1. **Native event loop integration** - cleaner, faster
2. **Hardware acceleration** available for properties
3. **Automatic cleanup** - no manual ID tracking
4. **Rich easing curves** - professional animations
5. **Better debugging** - Qt tools work properly
6. **Reduced dependency bloat** - one framework, not two

---

## Migration Patterns

### Pattern 1: Simple Delayed Call

**OLD (Tkinter)**:
```python
widget.after(1000, my_function)
```

**NEW (Qt)**:
```python
from PyQt6.QtCore import QTimer
QTimer.singleShot(1000, my_function)
```

---

### Pattern 2: Cancellable Delayed Call

**OLD (Tkinter)**:
```python
self._timer_id = widget.after(1000, my_function)
# Cancel:
widget.after_cancel(self._timer_id)
```

**NEW (Qt)**:
```python
from PyQt6.QtCore import QTimer
self._timer = QTimer()
self._timer.setSingleShot(True)
self._timer.timeout.connect(my_function)
self._timer.start(1000)
# Cancel:
self._timer.stop()
```

---

### Pattern 3: Periodic Updates (Recursive .after())

**OLD (Tkinter)**:
```python
def update_loop():
    # Do work
    self.update_display()
    # Schedule next update
    self._timer_id = widget.after(100, update_loop)

update_loop()
```

**NEW (Qt)**:
```python
from PyQt6.QtCore import QTimer
self._timer = QTimer()
self._timer.setInterval(100)
self._timer.timeout.connect(self.update_display)
self._timer.start()
# Stop: self._timer.stop()
```

---

### Pattern 4: Debouncing

**OLD (Tkinter)**:
```python
class Debouncer:
    def __init__(self, widget, callback, delay_ms=500):
        self.widget = widget
        self.callback = callback
        self.delay_ms = delay_ms
        self._after_id = None
    
    def trigger(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
        self._after_id = self.widget.after(self.delay_ms, self.callback)
```

**NEW (Qt)**:
```python
from src.ui.performance_utils_qt import DebouncedCallbackQt

debouncer = DebouncedCallbackQt(callback, delay_ms=500)
debouncer.trigger()  # Automatically cancels previous
```

---

### Pattern 5: Fade Animation

**OLD (Tkinter)**:
```python
def fade_out(alpha=1.0):
    if alpha <= 0:
        widget.destroy()
        return
    widget.wm_attributes('-alpha', alpha)
    widget.after(50, lambda: fade_out(alpha - 0.05))

widget.after(5000, fade_out)
```

**NEW (Qt)**:
```python
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve

# Smooth fade with easing
animation = QPropertyAnimation(widget, b"windowOpacity")
animation.setDuration(1000)
animation.setStartValue(1.0)
animation.setEndValue(0.0)
animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
animation.finished.connect(widget.close)

QTimer.singleShot(5000, animation.start)
```

---

### Pattern 6: UI Thread Updates

**OLD (Tkinter)**:
```python
# From background thread
widget.after(0, lambda: update_ui(data))
```

**NEW (Qt)**:
```python
from PyQt6.QtCore import QTimer, QMetaObject, Qt

# From background thread
QMetaObject.invokeMethod(widget, "update_ui", 
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(object, data))
```

Or simpler:
```python
QTimer.singleShot(0, lambda: widget.update_ui(data))
```

---

## Replacement Classes

### 1. ThrottledUpdateQt

Throttles rapid updates to prevent UI overload.

```python
from src.ui.performance_utils_qt import ThrottledUpdateQt

throttle = ThrottledUpdateQt(delay_ms=150)
throttle.schedule(my_update_function)  # Cancels previous
```

**Use Cases**:
- Slider value changes
- Text input updates
- Scroll position updates

---

### 2. DebouncedCallbackQt

Debounces callbacks - only fires after input stops.

```python
from src.ui.performance_utils_qt import DebouncedCallbackQt

debounce = DebouncedCallbackQt(my_callback, delay_ms=500)
debounce.trigger(arg1, arg2)  # Resets timer
```

**Use Cases**:
- Search as you type
- Auto-save on edit
- Preview updates

---

### 3. PeriodicUpdateQt

Periodic updates without recursive calls.

```python
from src.ui.performance_utils_qt import PeriodicUpdateQt

updater = PeriodicUpdateQt(interval_ms=1000, callback=my_function)
updater.start()
# Later: updater.stop()
```

**Use Cases**:
- Dashboard updates
- Progress monitoring
- Animation loops

---

## Qt Animation System

### QPropertyAnimation

Animates Qt properties smoothly.

```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

# Fade animation
fade = QPropertyAnimation(widget, b"windowOpacity")
fade.setDuration(1000)
fade.setStartValue(1.0)
fade.setEndValue(0.0)
fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
fade.start()

# Position animation
move = QPropertyAnimation(widget, b"pos")
move.setDuration(500)
move.setStartValue(QPoint(0, 0))
move.setEndValue(QPoint(100, 100))
move.setEasingCurve(QEasingCurve.Type.OutBounce)
move.start()
```

**Animatable Properties**:
- `windowOpacity` - Fade in/out
- `pos` - Move widget
- `geometry` - Resize/move
- `maximumHeight` - Expand/collapse
- Custom properties with Q_PROPERTY

---

### QParallelAnimationGroup

Run multiple animations simultaneously.

```python
from PyQt6.QtCore import QParallelAnimationGroup, QPropertyAnimation

group = QParallelAnimationGroup()

fade = QPropertyAnimation(widget, b"windowOpacity")
fade.setDuration(1000)
fade.setEndValue(0.0)

move = QPropertyAnimation(widget, b"pos")
move.setDuration(1000)
move.setEndValue(QPoint(100, 100))

group.addAnimation(fade)
group.addAnimation(move)
group.start()  # Both animations run together
```

---

### QSequentialAnimationGroup

Run animations in sequence.

```python
from PyQt6.QtCore import QSequentialAnimationGroup, QPropertyAnimation, QPauseAnimation

group = QSequentialAnimationGroup()

# Fade in
fade_in = QPropertyAnimation(widget, b"windowOpacity")
fade_in.setDuration(500)
fade_in.setEndValue(1.0)
group.addAnimation(fade_in)

# Wait
group.addPause(2000)

# Fade out
fade_out = QPropertyAnimation(widget, b"windowOpacity")
fade_out.setDuration(500)
fade_out.setEndValue(0.0)
group.addAnimation(fade_out)

group.start()
```

---

## Files Migrated

### Completed:
1. ✅ `achievement_display_qt_animated.py` - Fade animation with QPropertyAnimation
2. ✅ `performance_utils_qt.py` - Throttle, debounce, periodic timers

### Pending:
- [ ] `enemy_widget.py` - Animation and movement timers
- [ ] `performance_dashboard.py` - Update timer
- [ ] `batch_normalizer_panel.py` - Progress updates
- [ ] `quality_checker_panel.py` - Progress updates
- [ ] `alpha_fixer_panel.py` - Progress updates
- [ ] `color_correction_panel.py` - Progress updates
- [ ] `lineart_converter_panel.py` - Preview debounce

---

## Testing

### Test Animation
```python
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, QPropertyAnimation

app = QApplication([])
widget = QWidget()
widget.show()

# Test fade
anim = QPropertyAnimation(widget, b"windowOpacity")
anim.setDuration(2000)
anim.setStartValue(1.0)
anim.setEndValue(0.0)
QTimer.singleShot(1000, anim.start)

app.exec()
```

### Test Timer
```python
from PyQt6.QtCore import QTimer

def on_timeout():
    print("Timer fired!")

QTimer.singleShot(1000, on_timeout)
```

---

## Best Practices

1. **Use QTimer.singleShot()** for simple delays
2. **Use QPropertyAnimation** for smooth property changes
3. **Use QTimer with interval** for periodic updates (not recursive .after())
4. **Use QParallelAnimationGroup** for complex animations
5. **Store timer/animation references** to control them
6. **Connect to finished signal** for cleanup

---

## Performance Benefits

| Aspect | Tkinter .after() | Qt Native |
|--------|------------------|-----------|
| Event Loop | Separate | Integrated ✅ |
| Cancellation | Manual ID tracking | timer.stop() ✅ |
| Animations | Linear only | Rich easing ✅ |
| Performance | Good | Better ✅ |
| Debugging | Limited | Qt tools ✅ |
| Hardware Accel | No | Yes ✅ |

---

## Summary

Replace all tkinter `.after()` calls with Qt native timing:
- Simple delays → `QTimer.singleShot()`
- Periodic updates → `QTimer` with interval
- Animations → `QPropertyAnimation`
- Debouncing → `DebouncedCallbackQt`
- Throttling → `ThrottledUpdateQt`

This provides better performance, cleaner code, and proper Qt integration.
