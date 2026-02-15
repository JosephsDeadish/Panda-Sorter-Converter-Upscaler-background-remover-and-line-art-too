# Redundant Files to Remove After Migration

## Files to DELETE once Qt migration is complete:

### Deprecated Canvas-Based UI Files:

1. **src/ui/panda_widget.py**
   - Status: DEPRECATED (replaced by panda_widget_gl.py)
   - Reason: Canvas-based panda rendering (8000 lines)
   - Replacement: panda_widget_gl.py (OpenGL)
   - Action: DELETE after verification

2. **src/ui/dungeon_renderer.py**
   - Status: TO BE REPLACED
   - Reason: Canvas-based dungeon rendering
   - Replacement: qt_dungeon_viewport.py (QOpenGLWidget)
   - Action: DELETE after migration complete

3. **src/ui/enhanced_dungeon_renderer.py**
   - Status: TO BE REPLACED
   - Reason: Canvas-based enhanced dungeon
   - Replacement: qt_dungeon_viewport.py (QOpenGLWidget)
   - Action: DELETE after migration complete

4. **src/ui/enemy_widget.py**
   - Status: TO BE REPLACED
   - Reason: Canvas-based enemy rendering
   - Replacement: qt_enemy_widget.py (Qt QPainter)
   - Action: DELETE after migration complete

5. **src/ui/visual_effects_renderer.py**
   - Status: TO BE REPLACED
   - Reason: Canvas-based visual effects (16 refs)
   - Replacement: qt_visual_effects.py (to be created)
   - Action: DELETE after migration complete

### Demo Files Using Canvas:

6. **demo_combat_visual.py**
   - Status: Demo file with canvas
   - Reason: Uses old canvas system
   - Action: Either UPDATE to Qt or DELETE

7. **demo_dungeon.py**
   - Status: Demo file with canvas
   - Reason: Uses old canvas system
   - Action: Either UPDATE to Qt or DELETE

8. **demo_integrated_dungeon.py**
   - Status: Demo file with canvas
   - Reason: Uses old canvas system
   - Action: Either UPDATE to Qt or DELETE

### Test Files With Canvas Mocks:

9. **test_weapon_positioning.py**
   - Status: Uses mock canvas
   - Action: UPDATE to use Qt mocks or DELETE if no longer needed

---

## Files to KEEP (New Qt Versions):

### New Qt Widget Files:
- ✅ src/ui/panda_widget_gl.py (OpenGL panda)
- ✅ src/ui/panda_widget_loader.py (Auto-loader)
- ✅ src/ui/qt_achievement_popup.py (Qt popup)
- ✅ src/ui/qt_dungeon_viewport.py (Qt OpenGL dungeon)
- ✅ src/ui/qt_enemy_widget.py (Qt enemy display)
- ⏳ src/ui/qt_visual_effects.py (to be created)
- ✅ src/ui/pyqt6_base_panel.py (Qt base class)
- ✅ main_pyqt6.py (Qt main window)

---

## Removal Process:

### Step 1: Verify Replacement Complete
- [ ] All canvas code migrated to Qt
- [ ] All features working with Qt widgets
- [ ] No imports referencing old files

### Step 2: Update All Imports
Search and replace imports:
```python
# OLD (remove these)
from src.ui.panda_widget import PandaWidget
from src.ui.dungeon_renderer import DungeonRenderer
from src.ui.enhanced_dungeon_renderer import EnhancedDungeonRenderer
from src.ui.enemy_widget import EnemyWidget
from src.ui.visual_effects_renderer import VisualEffectsRenderer

# NEW (use these)
from src.ui.panda_widget_loader import PandaWidget
from src.ui.qt_dungeon_viewport import DungeonViewportWidget
from src.ui.qt_enemy_widget import EnemyDisplayWidget
from src.ui.qt_visual_effects import VisualEffectsWidget
```

### Step 3: Search for References
```bash
# Check for imports of old files
grep -r "from src.ui.panda_widget import" --include="*.py"
grep -r "from src.ui.dungeon_renderer import" --include="*.py"
grep -r "from src.ui.enemy_widget import" --include="*.py"
grep -r "from src.ui.visual_effects_renderer import" --include="*.py"
```

### Step 4: Remove Files
```bash
# Delete deprecated files
rm src/ui/panda_widget.py
rm src/ui/dungeon_renderer.py
rm src/ui/enhanced_dungeon_renderer.py
rm src/ui/enemy_widget.py
rm src/ui/visual_effects_renderer.py

# Optional: remove or update demos
rm demo_combat_visual.py
rm demo_dungeon.py
rm demo_integrated_dungeon.py
```

### Step 5: Update Documentation
- Remove references to canvas-based widgets
- Update README with Qt information
- Update installation docs for PyQt6

---

## Estimated Files to Remove:

**Primary UI Files**: 5 files (~3000+ lines)
**Demo Files**: 3 files (~500 lines)
**Test Files**: 1 file (update not remove)

**Total**: ~8 files to delete, ~3500 lines removed

---

## Safety Checks Before Removal:

- [ ] All tests passing with Qt widgets
- [ ] Application fully functional
- [ ] No broken imports
- [ ] Documentation updated
- [ ] User verification complete

---

## Timeline:

- **Phase 2-4**: Create all Qt replacements
- **Phase 5**: Update all imports
- **Phase 6**: Verify everything works
- **Final**: Remove redundant files

**This document tracks what to delete - will execute removal in Phase 6!**
