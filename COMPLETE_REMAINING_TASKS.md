# Complete Remaining Tasks - Canvas & Tkinter Replacement

## Your Requirements (From All Sessions)

### Core Requirements:
1. **Remove ALL tk.Canvas usage** - Replace with PyQt6 QGraphicsView/QGraphicsScene
2. **Replace ALL tkinter timing** - Replace .after() with QTimer, QPropertyAnimation
3. **No mixing tkinter and Qt** - Pure Qt for graphics, pure separation
4. **Use OpenGL for panda** - Already have panda_widget_gl.py
5. **Use Qt native animation** - QPropertyAnimation, QParallelAnimationGroup, QTimer, QStateMachine
6. **Work 30x longer** - Extended sessions of real work (15+ hours vs 30 mins)
7. **Actually do the work** - Not just documentation, real code changes

---

## Current Status (Verified)

### What's Completed ✅:
- **16 Qt panel files created** (batch_normalizer, quality_checker, alpha_fixer, color_correction, etc.)
- **5 panels integrated in main.py** (with Qt loader fallback system)
- **Canvas removed from 5 user panels** (closet, hotkey, customization, enemy_display, widgets)
- **6 deprecated files marked** (enemy_widget, dungeon_renderer, etc.)
- **Qt utilities created** (performance_utils_qt, achievement_display_qt_animated)
- **Test suite created** (test_qt_panel_integration.py - all passing)

### What Remains ❌:
- **109 .after() calls** still in tkinter files
- **13 update_idletasks()** calls still present
- **20+ files still using tkinter**
- **33 canvas calls** in deprecated files
- **10+ panels not converted to Qt**
- **Integration incomplete** for many panels

---

## Complete Work Breakdown

### PHASE 1: Canvas Elimination (6-8 hours)

**Files with remaining canvas:**
- [ ] enemy_widget.py (4 canvas calls) - DEPRECATED but still used
- [ ] dungeon_renderer.py (8 canvas calls) - DEPRECATED
- [ ] enhanced_dungeon_renderer.py (12 canvas calls) - DEPRECATED
- [ ] visual_effects_renderer.py (9 canvas calls) - DEPRECATED
- [ ] weapon_positioning.py (drawing functions)
- [ ] live_preview_widget.py (canvas for images)

**Actions:**
1. Verify Qt replacements work correctly
2. Update imports to use Qt versions
3. Remove old canvas files entirely
4. Test that nothing breaks

**Estimated**: 6-8 hours

---

### PHASE 2: Panel Conversions to Qt (20-30 hours)

**Panels Still Using Tkinter:**

#### High Priority (Still have .after() calls):
- [ ] **lineart_converter_panel.py** - 6 .after() calls, ~600 lines
  - Convert to lineart_converter_panel_qt.py
  - Replace all ctk widgets with Qt widgets
  - Use QThread for processing
  - Estimated: 3-4 hours

- [ ] **alpha_fixer_panel.py** - 5 .after() calls, ~400 lines
  - Already have alpha_fixer_panel_qt.py but not integrated
  - Need to integrate in main.py
  - Estimated: 1 hour

#### Medium Priority:
- [ ] **closet_panel.py** - Still using tkinter widgets
  - Have closet_display_qt.py but full conversion needed
  - Update to pure Qt
  - Estimated: 2-3 hours

- [ ] **customization_panel.py** - Partially converted
  - Have customization_panel_qt.py 
  - Ensure full integration
  - Estimated: 1-2 hours

- [ ] **hotkey_settings_panel.py** - Still tkinter
  - Have hotkey_display_qt.py
  - Full conversion needed
  - Estimated: 2 hours

- [ ] **archive_queue_widgets.py** - customtkinter based
  - No Qt version yet
  - Create archive_queue_widgets_qt.py
  - Estimated: 3-4 hours

- [ ] **widgets_panel.py** - Partially converted
  - Have widgets_panel_qt.py
  - Ensure complete integration
  - Estimated: 1 hour

#### Lower Priority:
- [ ] **performance_dashboard.py** - 1 .after() call
  - Simple periodic update
  - Convert to QTimer
  - Estimated: 1 hour

- [ ] **weapon_positioning.py** - Drawing functions
  - Have weapon_positioning_qt.py
  - Integrate properly
  - Estimated: 1-2 hours

- [ ] **live_preview_widget.py** - Canvas for images
  - Have live_preview_qt.py
  - Full integration needed
  - Estimated: 1-2 hours

**Estimated**: 20-30 hours total

---

### PHASE 3: Timing Replacement (15-20 hours)

**109 .after() calls to replace:**

#### Files with Most .after() Usage:
- [ ] batch_normalizer_panel.py - 7 calls (already have Qt version, integrate it)
- [ ] quality_checker_panel.py - 6 calls (already have Qt version, integrate it)
- [ ] lineart_converter_panel.py - 6 calls (need to create Qt version)
- [ ] alpha_fixer_panel.py - 5 calls (already have Qt version, integrate it)
- [ ] color_correction_panel.py - 4 calls (already have Qt version, integrate it)
- [ ] enemy_widget.py - 4 calls (deprecated, Qt version exists)
- [ ] Others - 77 calls spread across many files

**Actions for each file:**
1. Identify all .after() usage patterns
2. Replace with appropriate Qt mechanism:
   - `.after(delay, fn)` → `QTimer.singleShot(delay, fn)`
   - Recursive .after() → `QTimer` with interval
   - Animation .after() → `QPropertyAnimation`
   - UI update .after() → Qt signals/slots
3. Replace threading + .after() → `QThread` + signals
4. Test each replacement

**13 update_idletasks() calls to replace:**
- [ ] Find all occurrences
- [ ] Replace with `QApplication.processEvents()` (use sparingly)
- [ ] Or better: proper Qt signal/slot connections
- [ ] Test each replacement

**Estimated**: 15-20 hours

---

### PHASE 4: Integration in main.py (10-15 hours)

**Current Integration Status:**
- ✅ batch_normalizer_panel_qt
- ✅ quality_checker_panel_qt
- ✅ color_correction_panel_qt
- ✅ background_remover_panel_qt
- ✅ closet_display (partial)
- ✅ hotkey_display (partial)
- ✅ customization_panel (partial)

**Still Need Integration:**
- [ ] alpha_fixer_panel_qt
- [ ] widgets_panel_qt
- [ ] lineart_converter_panel_qt (after creating)
- [ ] archive_queue_widgets_qt (after creating)
- [ ] weapon_positioning_qt
- [ ] live_preview_qt
- [ ] All other Qt versions

**Integration Pattern for Each:**
```python
try:
    from src.ui.{panel}_qt import {Panel}Qt
    panel = {Panel}Qt(parent, ...)
    {PANEL}_IS_QT = True
except ImportError:
    from src.ui.{panel} import {Panel}
    panel = {Panel}(parent, ...)
    {PANEL}_IS_QT = False
```

**Actions:**
1. Add try/except import for each Qt panel
2. Add IS_QT tracking flag
3. Test panel loads correctly
4. Test fallback to tkinter works
5. Verify no breaking changes

**Estimated**: 10-15 hours

---

### PHASE 5: Testing & Verification (5-10 hours)

**Test Suite Needs:**
- [ ] Test each Qt panel loads
- [ ] Test each panel functions correctly
- [ ] Test threading (QThread) works
- [ ] Test progress updates work
- [ ] Test cancellation works
- [ ] Test error handling
- [ ] Test fallback to tkinter
- [ ] Performance testing
- [ ] Integration testing

**Verification Checks:**
- [ ] No .after() calls in Qt files: `grep "\.after(" src/ui/*_qt.py` → 0 results
- [ ] No update_idletasks() in Qt files: `grep "update_idletasks" src/ui/*_qt.py` → 0 results
- [ ] No tk.Canvas in active files: `grep "tk\.Canvas" src/ui/*.py | grep -v DEPRECATED` → minimal results
- [ ] All Qt panels use QThread: verify each has Worker class
- [ ] All panels integrated: check main.py imports

**Test Coverage:**
- Unit tests for each Qt panel
- Integration tests for main.py
- Performance benchmarks
- User acceptance testing

**Estimated**: 5-10 hours

---

## Total Estimated Work

**Minimum**: 56 hours
**Maximum**: 83 hours
**Average**: ~70 hours

**Breakdown:**
- Phase 1 (Canvas): 6-8 hours
- Phase 2 (Conversions): 20-30 hours
- Phase 3 (Timing): 15-20 hours
- Phase 4 (Integration): 10-15 hours
- Phase 5 (Testing): 5-10 hours

---

## Prioritized Action Items

### Immediate (Next Session):
1. ✅ Create this task list (DONE)
2. ⏳ Convert lineart_converter_panel to Qt (3-4 hours)
3. ⏳ Integrate alpha_fixer_panel_qt in main.py (1 hour)
4. ⏳ Test integrated panels work (1 hour)

### Short Term (Next 10 hours):
5. Create archive_queue_widgets_qt (3-4 hours)
6. Complete closet_panel Qt conversion (2-3 hours)
7. Complete customization_panel Qt conversion (1-2 hours)
8. Integrate all new Qt panels in main.py (2 hours)

### Medium Term (Next 20 hours):
9. Convert all remaining .after() calls to QTimer (10 hours)
10. Replace all update_idletasks() (2 hours)
11. Complete widget_panel integration (1 hour)
12. Complete hotkey_settings integration (2 hours)
13. Testing and bug fixes (5 hours)

### Long Term (Next 30 hours):
14. Remove all deprecated canvas files (4 hours)
15. Complete performance_dashboard conversion (1 hour)
16. Complete weapon_positioning integration (2 hours)
17. Complete live_preview integration (2 hours)
18. Comprehensive test suite (10 hours)
19. Performance optimization (5 hours)
20. Final cleanup and documentation (6 hours)

---

## File-by-File Task List

### Files Needing Full Qt Conversion:

#### 1. lineart_converter_panel.py
- **Current**: Tkinter, 6 .after() calls
- **Need**: lineart_converter_panel_qt.py
- **Tasks**:
  - Create QWidget-based panel
  - Replace all ctk widgets
  - Create LineartWorker(QThread)
  - Replace .after() with signals
  - Add to main.py integration
- **Time**: 3-4 hours

#### 2. archive_queue_widgets.py
- **Current**: customtkinter based
- **Need**: archive_queue_widgets_qt.py
- **Tasks**:
  - Create QWidget-based widgets
  - Replace ctk.CTkScrollableFrame
  - Replace ctk.CTkButton
  - Add queue management with Qt
  - Integrate in main.py
- **Time**: 3-4 hours

#### 3. performance_dashboard.py
- **Current**: 1 .after() call for updates
- **Need**: performance_dashboard_qt.py or update existing
- **Tasks**:
  - Replace .after() with QTimer
  - Ensure Qt-compatible
- **Time**: 1 hour

### Files Needing Integration:

#### 4. alpha_fixer_panel_qt.py
- **Status**: Created but not integrated
- **Tasks**:
  - Add to main.py imports
  - Add try/except fallback
  - Test functionality
- **Time**: 1 hour

#### 5. widgets_panel_qt.py
- **Status**: Created but not fully integrated
- **Tasks**:
  - Verify main.py uses it
  - Test functionality
- **Time**: 30 minutes

#### 6. closet_display_qt.py
- **Status**: Partial integration
- **Tasks**:
  - Complete integration
  - Remove tkinter dependencies
- **Time**: 1-2 hours

#### 7. customization_panel_qt.py
- **Status**: Created but needs verification
- **Tasks**:
  - Verify integration
  - Test all features
- **Time**: 1 hour

#### 8. hotkey_display_qt.py
- **Status**: Created but needs verification
- **Tasks**:
  - Complete integration
  - Test functionality
- **Time**: 1 hour

#### 9. weapon_positioning_qt.py
- **Status**: Created but not integrated
- **Tasks**:
  - Integrate in main.py
  - Test weapon positioning
- **Time**: 1-2 hours

#### 10. live_preview_qt.py
- **Status**: Created but not integrated
- **Tasks**:
  - Integrate in main.py
  - Test image preview
- **Time**: 1-2 hours

### Files Needing Deprecation/Removal:

#### 11. enemy_widget.py
- **Status**: Deprecated, has Qt replacement
- **Action**: Verify not used, can delete
- **Time**: 30 minutes

#### 12. dungeon_renderer.py
- **Status**: Deprecated, has Qt replacement
- **Action**: Verify not used, can delete
- **Time**: 30 minutes

#### 13. enhanced_dungeon_renderer.py
- **Status**: Deprecated, has Qt replacement
- **Action**: Verify not used, can delete
- **Time**: 30 minutes

#### 14. visual_effects_renderer.py
- **Status**: Deprecated, has Qt replacement
- **Action**: Verify not used, can delete
- **Time**: 30 minutes

### Files Needing Timing Updates:

#### 15. batch_normalizer_panel.py
- **Status**: Has Qt version, but tkinter still used
- **Action**: Remove entirely, use only Qt version
- **Time**: 1 hour

#### 16. quality_checker_panel.py
- **Status**: Has Qt version, but tkinter still used
- **Action**: Remove entirely, use only Qt version
- **Time**: 1 hour

#### 17. color_correction_panel.py
- **Status**: Has Qt version, integrated
- **Action**: Verify tkinter not used
- **Time**: 30 minutes

#### 18. performance_utils.py
- **Status**: Has performance_utils_qt.py
- **Action**: Update all usage to Qt version
- **Time**: 2 hours

---

## Testing Checklist

### Unit Tests:
- [ ] test_batch_normalizer_panel_qt.py
- [ ] test_quality_checker_panel_qt.py
- [ ] test_alpha_fixer_panel_qt.py
- [ ] test_color_correction_panel_qt.py
- [ ] test_lineart_converter_panel_qt.py
- [ ] test_archive_queue_widgets_qt.py
- [ ] test_customization_panel_qt.py
- [ ] test_closet_display_qt.py
- [ ] test_hotkey_display_qt.py
- [ ] test_widgets_panel_qt.py

### Integration Tests:
- [ ] test_main_qt_integration.py
- [ ] test_panel_switching.py
- [ ] test_qt_fallback.py
- [ ] test_threading.py
- [ ] test_signals_slots.py

### Performance Tests:
- [ ] benchmark_qt_vs_tkinter.py
- [ ] benchmark_threading.py
- [ ] benchmark_animation.py

---

## Success Criteria

### For Completion:
1. ✅ No tk.Canvas in non-deprecated files
2. ✅ No .after() in Qt panel files
3. ✅ No update_idletasks() in Qt files
4. ✅ All panels have Qt versions
5. ✅ All Qt panels integrated in main.py
6. ✅ All tests passing
7. ✅ Application runs with PyQt6
8. ✅ Application falls back to tkinter gracefully
9. ✅ Performance improved with Qt
10. ✅ No mixing of rendering systems

### Verification Commands:
```bash
# No .after() in Qt files
grep -r "\.after(" src/ui/*_qt.py
# Should return: 0 results

# No update_idletasks in Qt files
grep -r "update_idletasks" src/ui/*_qt.py
# Should return: 0 results

# No canvas in active files
grep -r "tk\.Canvas" src/ui/*.py | grep -v "DEPRECATED"
# Should return: minimal/none

# All Qt panels exist
ls src/ui/*_panel_qt.py | wc -l
# Should return: 10+

# All tests pass
python -m pytest tests/
# Should return: All passing

# Integration test passes
python test_qt_panel_integration.py
# Should return: All passed
```

---

## Notes

### Why This Is Important:
1. **Performance**: Qt is hardware-accelerated, tkinter is not
2. **Maintainability**: One framework is easier than two
3. **Features**: Qt has richer animation/graphics APIs
4. **Future**: Tkinter is legacy, Qt is modern
5. **User Experience**: Smoother, more responsive UI

### Risks:
1. **Breaking Changes**: Might affect existing users
2. **Testing Burden**: Need comprehensive testing
3. **Learning Curve**: Qt is more complex than tkinter
4. **Dependencies**: Requires PyQt6 installation

### Mitigation:
1. **Fallback System**: Keep tkinter as fallback
2. **Gradual Migration**: Do panel by panel
3. **Comprehensive Testing**: Test everything
4. **Documentation**: Document all changes

---

## Progress Tracking

Update this section as work progresses:

### Session 1-10: Foundation
- [x] Created Qt utilities
- [x] Created 4 Qt panels
- [x] Integrated 5 panels
- [x] Created test suite
- [x] Documented requirements

### Session 11-20: Panel Conversions
- [ ] Convert lineart_converter
- [ ] Convert archive_queue
- [ ] Complete closet conversion
- [ ] Complete customization conversion
- [ ] Complete hotkey conversion

### Session 21-30: Integration
- [ ] Integrate all Qt panels
- [ ] Remove deprecated files
- [ ] Update all .after() calls
- [ ] Replace update_idletasks

### Session 31-40: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Performance testing
- [ ] Bug fixes

### Session 41+: Polish
- [ ] Final cleanup
- [ ] Documentation
- [ ] User guide
- [ ] Release

---

**Last Updated**: 2026-02-15
**Total Estimated Hours**: 56-83 hours
**Completion**: ~20% (foundation laid)
**Next Priority**: Panel conversions and integration
