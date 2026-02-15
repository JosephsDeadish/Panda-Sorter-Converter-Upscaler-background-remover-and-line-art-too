# Complete Canvas Usage Inventory

## Comprehensive search of ALL canvas usage in the codebase

Generated: 2026-02-15

---

## Files With Canvas Usage:

### Main Application:
1. **main.py** - 5 canvas instances
   - Achievement popup canvas (line 7417)
   - Dungeon renderer canvas (line 9738)
   - Enemy display canvas (line 10058)
   - Enemy drawing function (line 10250)
   - Travel animation canvas (line 10582)

### UI Modules (src/ui/):
2. **panda_widget.py** - 10 canvas references
   - Main panda rendering (DEPRECATED - migrated to OpenGL)
   
3. **visual_effects_renderer.py** - 16 canvas references
   - Combat effects rendering
   - Projectile rendering
   - Visual effects system
   
4. **dungeon_renderer.py** - 1 canvas reference
   - Basic dungeon rendering
   
5. **enhanced_dungeon_renderer.py** - 1 canvas reference
   - Enhanced dungeon rendering
   
6. **enemy_widget.py** - 1 canvas reference
   - Enemy widget rendering
   
7. **customization_panel.py** - 2 canvas references
   - Color preview canvas
   - Customization preview
   
8. **closet_panel.py** - 1 canvas reference
   - Clothing preview
   
9. **widgets_panel.py** - 1 canvas reference
   - Widget/item preview
   
10. **hotkey_settings_panel.py** - 1 canvas reference
    - Hotkey visual preview

### Feature Modules (src/features/):
11. **preview_viewer.py** - Canvas usage
    - Image preview system

### Demo/Test Files:
12. **demo_combat_visual.py** - Canvas usage
13. **demo_dungeon.py** - Canvas usage
14. **demo_integrated_dungeon.py** - Canvas usage
15. **test_weapon_positioning.py** - Mock canvas

---

## Migration Status:

### ✅ COMPLETED:
- [x] Static panda preview (main.py) - REMOVED
- [x] Panda widget main rendering - MIGRATED to OpenGL
- [x] Qt achievement popup created
- [x] Qt dungeon viewport created
- [x] Qt enemy widget created

### ⏳ IN PROGRESS (Phase 2):
- [ ] Achievement popup in main.py - Replace with Qt widget
- [ ] Travel animation in main.py - Replace with Qt animation
- [ ] Dungeon renderer in main.py - Replace with Qt viewport
- [ ] Enemy display in main.py - Replace with Qt widget

### ⏳ TO DO (Phase 3 - Game Rendering):
- [ ] visual_effects_renderer.py (16 canvas refs) - OpenGL or Qt graphics
- [ ] dungeon_renderer.py (1 ref) - Qt OpenGL viewport
- [ ] enhanced_dungeon_renderer.py (1 ref) - Qt OpenGL viewport
- [ ] enemy_widget.py (1 ref) - Qt widget

### ⏳ TO DO (Phase 4 - Tool Panels):
- [ ] customization_panel.py (2 refs) - Qt color picker
- [ ] closet_panel.py (1 ref) - Qt list/grid widget
- [ ] widgets_panel.py (1 ref) - Qt list/grid widget
- [ ] hotkey_settings_panel.py (1 ref) - Qt graphics or remove
- [ ] preview_viewer.py - Qt QLabel with QPixmap

### 📝 Demo/Test Files:
- [ ] demo_combat_visual.py - Update to use Qt
- [ ] demo_dungeon.py - Update to use Qt
- [ ] demo_integrated_dungeon.py - Update to use Qt
- [ ] test_weapon_positioning.py - Update mocks

---

## Total Canvas Components:

**Files with Canvas**: 15+ files
**Canvas Instances**: ~50+ references
**Major Components**: 12 primary UI components

---

## Priority Order:

### Priority 1 (Critical - User-Facing):
1. ✅ Panda widget (DONE - OpenGL)
2. ⏳ Achievement popup (Qt widget created)
3. ⏳ Enemy displays (Qt widget created)
4. ⏳ Dungeon renderer (Qt viewport created)

### Priority 2 (Game Features):
5. ⏳ Visual effects renderer (16 refs)
6. ⏳ Combat animations
7. ⏳ Travel animations

### Priority 3 (Tool Panels):
8. ⏳ Customization preview
9. ⏳ Closet preview
10. ⏳ Widgets panel preview
11. ⏳ Hotkey preview

### Priority 4 (Optional):
12. ⏳ Demo files
13. ⏳ Test files

---

## Migration Approach by Component:

### 3D Scenes → QOpenGLWidget:
- Dungeon renderer
- Combat arena
- Visual effects (3D)
- Panda widget (DONE)

### 2D UI → Qt Widgets:
- Achievement popups (QDialog)
- Color previews (QColorDialog)
- Item previews (QLabel + QPixmap)
- Enemy displays (QLabel + QPixmap)

### Animations → Qt Animation Framework:
- Travel animations (QPropertyAnimation)
- UI transitions (QPropertyAnimation)
- Effects (QGraphicsEffect)

### Image Previews → QLabel + QPixmap:
- Clothing previews
- Widget previews
- Color previews
- General image displays

---

## Estimated Work:

**Phase 2 (Main.py)**: ~8 hours
- 5 canvas components
- Integration work
- Testing

**Phase 3 (Game Rendering)**: ~20 hours
- 4 major rendering files
- OpenGL migration for 3D
- Complex visual effects

**Phase 4 (Tool Panels)**: ~12 hours
- 5 panel files
- Qt widget replacements
- Preview systems

**Phase 5 (Integration)**: ~6 hours
- Connect all components
- Test all features
- Bug fixes

**Phase 6 (Cleanup)**: ~3 hours
- Remove canvas code
- Update documentation
- Final verification

**Total**: ~50 hours remaining

---

## Architecture Guidelines:

### ✅ CORRECT:
```
Qt Widget
├── Qt Standard Widgets (buttons, labels, etc.)
├── QOpenGLWidget (only for 3D scenes)
└── QLabel + QPixmap (for 2D images/previews)
```

### ❌ INCORRECT:
- Drawing UI in OpenGL
- Building buttons in 3D engine
- Mixing UI and rendering logic

---

## Next Actions:

1. **Immediate**: Finish Phase 2 (main.py integration)
2. **Next**: Phase 3 (game rendering files)
3. **Then**: Phase 4 (tool panel previews)
4. **Finally**: Phases 5-6 (integration & cleanup)

---

## Progress Tracking:

- **Files Migrated**: 1/15 (6.7%)
- **Components Migrated**: 4/50 (8%)
- **Phases Complete**: 1/6 (16.7%)
- **Estimated Completion**: ~50 hours remaining

---

*This inventory ensures NOTHING is missed in the canvas-to-Qt migration.*
