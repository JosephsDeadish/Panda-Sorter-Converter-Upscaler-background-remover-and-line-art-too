# CRITICAL ISSUES REMAINING - Action Plan

## Date: 2026-02-18

---

## ISSUE 1: AI Suggested/Manual Mode Not Working ⚠️

### Current State
The code EXISTS but UI may not be properly visible/functional:
- ✅ Code exists in `src/ui/organizer_panel_qt.py`
- ✅ _run_suggested() method (line 197)
- ✅ _run_manual() method (line 244)  
- ✅ classification_ready signal (line 93)
- ✅ _handle_classification() method (line 1322)
- ✅ UI widgets created (lines 590-653):
  - suggestion_label
  - confidence_label
  - good_btn (✅ Good feedback)
  - bad_btn (❌ Bad feedback)
  - folder_input (manual override)
  - suggestions_list (autocomplete)
  - path_preview_label

### Problem
UI components exist but may not be:
1. Visible when mode is selected
2. Properly connected to signals
3. Receiving classification_ready events
4. Showing in correct layout

### How to Fix
1. **Verify Signal Connection**:
   - Check that `classification_ready` signal connects to `_handle_classification` slot
   - Location: Should be in `__init__` or widget creation
   
2. **Check Visibility**:
   - UI section is in a QSplitter (lines 645-649)
   - May be collapsed or not shown
   - Check if preview/classification containers are visible by default

3. **Test Flow**:
   - Select "💡 Suggested" or "✍️ Manual" mode
   - Click organize button
   - Worker thread should emit classification_ready
   - _handle_classification should update UI
   - Widgets should become visible/enabled

### Code to Add
```python
# In __init__ or _create_classification_section, add:
self.worker_thread.classification_ready.connect(self._handle_classification)

# Make sure containers are visible:
preview_container.setVisible(True)
classification_container.setVisible(True)
```

---

## ISSUE 2: Missing Archive Input Checkbox for ALL Tools ❌

### Current State
**MISSING** from all tool panels except organizer

### What's Needed
Every tool panel needs:
```python
# Add to file selection section:
self.input_is_archive_cb = QCheckBox("📦 Input is Archive (.zip, .7z, .rar)")
self.input_is_archive_cb.setChecked(False)
self._set_tooltip(self.input_is_archive_cb, "input_archive_checkbox")
file_selection_layout.addWidget(self.input_is_archive_cb)
```

### Panels to Update
1. background_remover_panel_qt.py
2. color_correction_panel_qt.py
3. alpha_fixer_panel_qt.py
4. upscaler_panel_qt.py
5. lineart_converter_panel_qt.py
6. batch_normalizer_panel_qt.py
7. quality_checker_panel_qt.py
8. image_repair_panel_qt.py
9. batch_rename_panel_qt.py

Note: organizer_panel_qt.py already has archive support (archive_input_cb line 543)

---

## ISSUE 3: Missing Archive Output Checkbox ❌

### Current State
**PARTIALLY** exists:
- organizer_panel_qt.py HAS archive_output_cb (line 546)
- Other panels DON'T have it

### What's Needed
Every tool panel needs:
```python
# Add to output section:
self.output_to_archive_cb = QCheckBox("📦 Export to Archive")
self.output_to_archive_cb.setChecked(False)
self._set_tooltip(self.output_to_archive_cb, "output_archive_checkbox")
output_layout.addWidget(self.output_to_archive_cb)

# Archive format selector:
self.archive_format_combo = QComboBox()
self.archive_format_combo.addItems(["ZIP", "7Z", "TAR.GZ"])
self.archive_format_combo.setEnabled(False)
self.output_to_archive_cb.toggled.connect(
    lambda checked: self.archive_format_combo.setEnabled(checked)
)
output_layout.addWidget(self.archive_format_combo)
```

---

## ISSUE 4: Missing Tooltips for Archive Features ❌

### Tooltip IDs Needed
Add to `src/features/tutorial_system.py` in _PANDA_TOOLTIPS dict:

```python
'input_archive_checkbox': {
    'normal': [
        "Check this if your input is an archive file (.zip, .7z, .rar)",
        "Enable archive input mode to process files from compressed archives",
        "Extract and process files from archive automatically",
    ],
    'vulgar': [
        "Got a zip file? Check this shit. The panda will unzip it for you. Like a digital strip tease but less fun.",
        "Archive input. For when your textures are compressed like your will to live.",
        "Check this if you're too lazy to unzip the damn file yourself. We got you.",
    ]
},
'output_archive_checkbox': {
    'normal': [
        "Save results to an archive file instead of a folder",
        "Package output into a compressed archive",
        "Create archive with processed files",
    ],
    'vulgar': [
        "Zip up your output like you're packing for a trip you'll never take.",
        "Archive output. Because folders are so last century. Compress that shit.",
        "Make a zip file of your results. Tidy. Efficient. Unlike your desktop.",
    ]
},
'ai_suggestion_label': {
    'normal': [
        "AI's suggested folder for this texture based on analysis",
        "Machine learning classification suggestion",
        "Recommended destination folder from AI",
    ],
    'vulgar': [
        "The AI thinks this goes here. It's probably right. It's smarter than you.",
        "AI suggestion. Take it or leave it. The AI doesn't care about your feelings.",
        "Machine learning says: put it here. Or don't. Rebel against the machines.",
    ]
},
'feedback_good_button': {
    'normal': [
        "Accept this suggestion and let the AI learn from your choice",
        "Confirm the AI's suggestion is correct",
        "Mark this classification as good and continue",
    ],
    'vulgar': [
        "AI got it right. Good panda. Click this to pat it on the head. Virtually.",
        "Suggestion is good. AI wins this round. Click to continue.",
        "Yeah, that's right. Good guess, robot. Now do the next one.",
    ]
},
'feedback_bad_button': {
    'normal': [
        "Reject this suggestion and teach the AI the correct answer",
        "This suggestion is wrong - provide the right folder",
        "Mark as incorrect and input the correct destination",
    ],
    'vulgar': [
        "AI fucked up. Click this and tell it where it SHOULD go. Tough love.",
        "Wrong answer, robot. Try again. Or let the human fix it. As usual.",
        "Bad panda. No bamboo for you. Click and show it the right way.",
    ]
},
'manual_override_input': {
    'normal': [
        "Type your own folder name to override the AI suggestion",
        "Enter custom destination folder",
        "Manual folder path input",
    ],
    'vulgar': [
        "Don't like the AI's suggestion? Type your own damn folder here. Show it who's boss.",
        "Manual override. For when you know better than the machine. Spoiler: you probably don't.",
        "Type where YOU think it should go. The AI will learn from your wisdom. Or mistakes.",
    ]
},
```

---

## ISSUE 5: Missing Recursive Search Checkbox (Organizer) ❌

### Current State
- Line 266: `recursive = self.settings.get('recursive', True)` - HARDCODED
- No UI control for users

### What to Add
```python
# In _create_input_selection_section:
self.recursive_search_cb = QCheckBox("🔍 Recursive Search (include subfolders)")
self.recursive_search_cb.setChecked(True)
self._set_tooltip(self.recursive_search_cb, "recursive_search_checkbox")
input_layout.addWidget(self.recursive_search_cb)
```

Then update line 266:
```python
recursive = self.recursive_search_cb.isChecked()
```

---

## SUMMARY OF WORK NEEDED

### High Priority (Blocking Features)
1. ⚠️ **Fix AI mode visibility** (1-2 hours)
   - Debug why classification UI not showing
   - Ensure signal connections work
   - Test suggested/manual modes

2. ❌ **Add archive input checkbox** to 9 panels (2-3 hours)
   - Add checkbox to each panel
   - Connect to file handling logic
   - Add tooltips

3. ❌ **Add archive output checkbox** to 9 panels (2-3 hours)
   - Add checkbox + format selector
   - Connect to save logic
   - Add tooltips

### Medium Priority
4. ❌ **Add recursive checkbox** to organizer (30 min)
   - Simple checkbox addition
   - Update hardcoded line

5. ❌ **Add all missing tooltips** (1-2 hours)
   - Add tooltip definitions to tutorial_system.py
   - Call _set_tooltip on all new widgets

### Total Estimated Time: 8-12 hours

---

## QUICK WINS (Can Do Now)

### 1. Add Recursive Checkbox (30 minutes)
File: `src/ui/organizer_panel_qt.py`
Line: ~266

### 2. Add Archive Tooltips (1 hour)  
File: `src/features/tutorial_system.py`
Add all tooltip definitions

### 3. Verify Signal Connection (30 minutes)
File: `src/ui/organizer_panel_qt.py`
Check __init__ for classification_ready.connect()

---

## TESTING CHECKLIST

After fixes:
- [ ] AI Suggested mode shows classification UI
- [ ] AI Manual mode shows classification UI
- [ ] Good/Bad feedback buttons work
- [ ] Folder suggestions appear as you type
- [ ] Archive input checkbox appears on all tools
- [ ] Archive output checkbox appears on all tools
- [ ] Archive format selector enabled when checkbox checked
- [ ] Recursive search checkbox works in organizer
- [ ] All tooltips show on hover
- [ ] All three tooltip modes work (Normal, Dumbed Down, Unhinged Panda)

---

## FILES TO MODIFY

1. **src/ui/organizer_panel_qt.py** - Fix AI mode, add recursive checkbox
2. **src/ui/background_remover_panel_qt.py** - Add archive checkboxes
3. **src/ui/color_correction_panel_qt.py** - Add archive checkboxes
4. **src/ui/alpha_fixer_panel_qt.py** - Add archive checkboxes
5. **src/ui/upscaler_panel_qt.py** - Add archive checkboxes
6. **src/ui/lineart_converter_panel_qt.py** - Add archive checkboxes
7. **src/ui/batch_normalizer_panel_qt.py** - Add archive checkboxes
8. **src/ui/quality_checker_panel_qt.py** - Add archive checkboxes
9. **src/ui/image_repair_panel_qt.py** - Add archive checkboxes
10. **src/ui/batch_rename_panel_qt.py** - Add archive checkboxes
11. **src/features/tutorial_system.py** - Add tooltip definitions

**Total**: 11 files to modify

---

## CONCLUSION

The infrastructure is there (tooltip system, archive support in organizer), but needs to be:
1. Debugged (AI mode UI)
2. Replicated across all panels (archive checkboxes)
3. Connected (tooltips for new features)

This is systematic work that follows established patterns. Each panel modification is similar.
