# Manual Validation Checklist

## Before Testing
- [ ] Backup your config file at `~/.ps2_texture_sorter/config.json`
- [ ] Prepare test texture files with LOD naming (e.g., `texture_lod0.dds`, `texture_lod1.dds`)

## Test 1: LOD Detector Crash (CRITICAL)
- [ ] Launch application
- [ ] Select input directory with texture files
- [ ] Select output directory
- [ ] **Enable "Detect LODs" checkbox**
- [ ] Click "Start Sorting"
- [ ] **Expected:** Sorting completes without AttributeError
- [ ] **Expected:** Log shows "Detecting LOD groups..." and "Found X LOD groups"

## Test 2: Settings Window Focus
- [ ] Click "⚙️ Settings" button
- [ ] **Expected:** Settings window appears on top of main window
- [ ] Try clicking main window
- [ ] **Expected:** Cannot interact with main window (modal behavior)
- [ ] Close settings window
- [ ] **Expected:** Main window becomes interactive again

## Test 3: Tutorial System
- [ ] Delete config file to trigger first-run
- [ ] Launch application
- [ ] **Expected:** Tutorial overlay appears with semi-transparent background
- [ ] **Expected:** Tutorial window is clickable and on top
- [ ] Complete or skip tutorial
- [ ] Go to Settings → Click "🎓 Tutorial" button to re-run
- [ ] **Expected:** Tutorial appears again

## Test 4: Settings Apply
- [ ] Open Settings
- [ ] Change theme (Dark ↔ Light)
- [ ] Change UI scale (100% → 125%)
- [ ] Change tooltip mode
- [ ] Change cursor style
- [ ] Click "💾 Save Settings"
- [ ] **Expected:** Theme changes immediately
- [ ] **Expected:** UI scale changes immediately
- [ ] **Expected:** Success message appears
- [ ] Restart app and verify settings persisted

## Test 5: Tooltips
- [ ] Hover over "Start Sorting" button
- [ ] **Expected:** Tooltip appears after ~0.5 seconds
- [ ] Hover over input/output browse buttons
- [ ] **Expected:** Tooltips appear
- [ ] Hover over "Organize" button
- [ ] **Expected:** Tooltip appears

## Test 6: Note Deletion
- [ ] Navigate to "📝 Notepad" tab
- [ ] Create a second note tab
- [ ] Select a note tab
- [ ] Click "🗑️ Delete Current Note"
- [ ] **Expected:** Confirmation dialog appears
- [ ] Confirm deletion
- [ ] **Expected:** Note tab is removed
- [ ] **Expected:** Notes are saved automatically

## Test 7: App Icon (Build Test)
- [ ] Run: `pyinstaller build_spec.spec`
- [ ] Navigate to `dist/` folder
- [ ] Check `PS2TextureSorter.exe` properties
- [ ] **Expected:** Panda icon visible on EXE file

## Test 8: File Browser
- [ ] Navigate to "📁 Browser" tab
- [ ] Click "📂 Browse Directory"
- [ ] Select a folder with many files (>100)
- [ ] **Expected:** All files shown (no 100 limit)
- [ ] Check "Show all files" checkbox
- [ ] **Expected:** Non-texture files now visible
- [ ] Double-click on "⬆️ .. (Parent Directory)"
- [ ] **Expected:** Navigate to parent folder
- [ ] Double-click on a folder name
- [ ] **Expected:** Navigate into that folder
- [ ] Check status bar at bottom
- [ ] **Expected:** Shows file and folder count

## Test 9: Sound Effects
- [ ] Open Settings
- [ ] Enable "Play sound effects"
- [ ] Enable "Alert on operation completion"
- [ ] Save settings
- [ ] Start a texture sorting operation
- [ ] Wait for completion
- [ ] **Expected (Windows):** System asterisk sound plays
- [ ] **Expected (Unix/Mac):** Bell sound/beep

## Test 10: Error Dialog
- [ ] Create an invalid scenario (e.g., select read-only output directory)
- [ ] Start sorting
- [ ] **Expected:** Error dialog appears with message
- [ ] **Expected:** Log shows detailed error with traceback
- [ ] Click OK on error dialog
- [ ] **Expected:** Application remains functional

## Post-Testing
- [ ] Check log file at `~/.ps2_texture_sorter/logs/` for errors
- [ ] Verify all settings were saved correctly
- [ ] Test that application can be closed and reopened without issues

---

## Known Limitations (Not Fixed)
These were mentioned in the issue but are beyond the scope of minimal fixes:

- Tutorial widget highlighting (target_widget) not implemented - requires widget registry
- Custom sound files not supported - only system beeps
- File browser search/filter bar not added
- File preview not added
- Cursor styles beyond config storage not fully implemented

---

## Success Criteria
✅ All 10 critical issues fixed
✅ Application runs without crashes
✅ Settings persist and apply correctly
✅ User experience significantly improved
✅ No regressions introduced

---

**If any test fails, check the log file and report the issue with:**
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Log file contents
