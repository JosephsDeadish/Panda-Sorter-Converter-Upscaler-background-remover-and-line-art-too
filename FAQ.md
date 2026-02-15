# Frequently Asked Questions (FAQ) 🐼

## General Questions

### Q: What is Game Texture Sorter?
A: Game Texture Sorter is a professional application for automatically sorting and organizing game texture dumps from PS2 and other platforms. It uses AI to classify textures into 50+ categories and includes powerful tools for background removal, object removal, and batch processing.

### Q: Do I need programming knowledge to use this?
A: No! The application has a user-friendly GUI. Just download, run the .exe, and start sorting textures.

### Q: Which games are supported?
A: The app automatically recognizes 70+ PS2 games and can handle textures from any game. It includes specific texture profiles for popular titles.

### Q: Can I use this for HD/4K textures?
A: Yes! The application supports both PS2 textures (512x512 and smaller) and modern HD/4K textures with conditional preprocessing.

## AI-Powered Tools

### Q: What AI features are available?
A: Two main AI tools:
1. **Background Remover** - Remove backgrounds to create transparent PNGs
2. **Object Remover** - Paint objects to remove them from images

### Q: Do I need internet for AI features?
A: No! All AI processing runs locally on your computer. No internet required.

### Q: Which AI models are available?
A: Four models for background removal:
- **U2-Net** - Fast, general purpose (default)
- **U2-Net Portrait** - Optimized for faces
- **ISNet-general** - Higher quality for complex scenes
- **ISNet-anime** - Best for anime-style art

### Q: How do I choose the right preset for background removal?
A:
- **PS2 Textures** - Sharp, pixelated game assets
- **Gaming Assets** - 2D sprites and UI elements
- **Photography** - Real photos with natural edges
- **Art/Illustration** - Drawings with smooth gradients
- **UI Elements** - Icons and interface graphics
- **3D Character Models** - Characters with hair/fur
- **Transparent Objects** - Glass, smoke, translucent materials
- **Pixel Art** - Retro pixel-perfect preservation

## Background Remover

### Q: My edges look rough/choppy. How do I fix them?
A: Increase the edge refinement slider (feathering) to 5-10px for smoother edges.

### Q: I'm losing important pixels at the edges. Help!
A: Increase edge dilation to expand the mask outward, or use a different alpha preset.

### Q: There's a colored halo around my object. How do I remove it?
A: Enable "Color fringe removal" in advanced settings. This removes colored halos from leftover background.

### Q: Can I process multiple images at once?
A: Yes! Select multiple files or an entire folder. Use the processing queue to manage large batches.

### Q: Can I process ZIP/RAR archives directly?
A: Yes! Click "Select Archive" to process entire archives without extracting them first.

### Q: What formats can I save as?
A: PNG (recommended for transparency), TIFF (16-bit alpha), or WebP (smaller file size with transparency).

## Object Remover

### Q: How do I use the Object Remover?
A:
1. Switch to "Object Remover" mode
2. Click "Start Painting" to enable brush
3. Paint over the object you want to remove (red highlight)
4. Click "Remove Highlighted Object"
5. Wait for AI processing (5-30 seconds)

### Q: Which selection tool should I use?
A:
- **Brush** - Freehand painting for irregular shapes
- **Rectangle** - Quick selection of rectangular areas
- **Lasso** - Freehand polygon selection
- **Magic Wand** - Click to select similar colors automatically

### Q: How does brush opacity work?
A: Lower opacity (30-50%) builds up the mask gradually for better control. Full opacity (100%) paints at full strength for quick masking.

### Q: Can I undo mistakes?
A: Yes! Use the Undo button (Ctrl+Z) to remove the last stroke. The Redo button (Ctrl+Y) restores undone strokes. History stores up to 50 actions.

### Q: The AI removal didn't work perfectly. What now?
A: Try again! AI results vary each attempt. You can also paint additional areas and remove again, or use a different AI model.

## Tooltips

### Q: What are the different tooltip modes?
A: Three modes:
1. **Normal** - Professional, detailed explanations
2. **Dumbed-Down** - Simple, accessible language
3. **Cursing/Unhinged** - Profane yet helpful (unlockable)

### Q: How do I unlock cursing tooltips?
A: Process 200 files or unlock 10 items to unlock the cursing/unhinged tooltip mode.

### Q: Can I disable tooltips?
A: Tooltips appear automatically when you hover over controls. They don't interfere with workflow.

## Performance

### Q: The application is slow. How do I speed it up?
A:
- Enable GPU acceleration in Advanced Settings (3-5x faster)
- Increase thread count (4-8) for batch processing
- Use faster AI models (U2-Net instead of ISNet)
- Process smaller batches

### Q: How much RAM do I need?
A: Minimum 4GB, recommended 8GB+. For massive texture sets (100k+ files), 16GB recommended.

### Q: Does this work on Mac/Linux?
A: Currently Windows only. The Python source can run on Mac/Linux but the pre-built executable is Windows-only.

### Q: Can I run this on a laptop?
A: Yes! It works on any Windows laptop. Performance depends on CPU/GPU specs. Integrated graphics work but dedicated GPU is faster.

## Panda Companion

### Q: What does the panda do?
A: The panda is your interactive companion! Pet it, feed it, drag it around, or just watch it animate. It levels up as you use the app.

### Q: How do I feed the panda?
A: Click the feed button or right-click the panda to access feeding options.

### Q: Can I customize the panda?
A: Yes! Unlock outfits, hats, and accessories through achievements and the in-app shop.

### Q: The panda disappeared! Where is it?
A: Click the Panda icon in the toolbar to show/hide the panda widget. It starts in the bottom-right corner and stays visible even in fullscreen.

## Troubleshooting

### Q: "Background removal not available" error?
A: Install the required package with CPU or GPU backend:
```bash
# For CPU (recommended)
pip install "rembg[cpu]"

# For GPU (NVIDIA/CUDA)
pip install "rembg[gpu]"
```

### Q: The app won't start. What do I do?
A: 
1. Check Windows Defender didn't block it
2. Run as Administrator
3. Check the logs in the logs/ folder
4. See TROUBLESHOOTING.md for detailed steps

### Q: Processing failed for some images. Why?
A: Check the error log for details. Common issues:
- Corrupted image files
- Unsupported format
- Out of memory (try smaller batches)

### Q: Can I use this commercially?
A: Check the LICENSE file for usage terms. (Currently: TBD)

### Q: Where are my processed files saved?
A: By default, in the same folder as the source files with "_nobg" suffix. You can change the output directory in settings.

### Q: The preview isn't updating. What's wrong?
A: Try:
1. Click "Refresh Preview"
2. Reload the image
3. Restart the application if issue persists

## Advanced Features

### Q: What are alpha presets?
A: Pre-configured settings optimized for different image types. They control how edges are detected and transparency is applied.

### Q: What is alpha matting?
A: A technique for handling semi-transparent objects like glass, smoke, or hair. Enable it for better results with translucent materials.

### Q: Can I create custom presets?
A: Currently no, but you can manually adjust edge refinement, thresholds, and other settings to match your needs.

### Q: What's the difference between edge dilation and erosion?
A:
- **Dilation** - Expands the mask outward (keeps more pixels)
- **Erosion** - Shrinks the mask inward (removes edge pixels)

### Q: How do I get the best results?
A:
1. Choose the right preset for your image type
2. Adjust edge refinement if needed
3. Enable alpha matting for transparent objects
4. Preview before batch processing
5. Try different AI models if results aren't perfect

## Getting Help

### Q: Where can I find more documentation?
A: Check the docs/ folder for detailed guides on specific features.

### Q: How do I report a bug?
A: Create an issue on the repository with:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Log files from logs/ folder

### Q: Can I request a feature?
A: Yes! Open a feature request issue. Popular requests may be implemented in future versions.

### Q: Is there a tutorial?
A: Yes! Press F1 anywhere in the app for context-sensitive help, or check the built-in tutorial system.

## Tips & Tricks

### 💡 Pro Tip: Keyboard Shortcuts
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `[` / `]` - Decrease/Increase brush size
- `F1` - Help
- `Esc` - Cancel operation

### 💡 Pro Tip: Batch Processing
Always preview the first image before processing hundreds of files. Adjust settings based on preview results.

### 💡 Pro Tip: Archive Processing
Process archives directly instead of extracting - it's faster and maintains folder structure.

### 💡 Pro Tip: Selection Tools
- Use Rectangle for UI elements and logos
- Use Lasso for irregular shapes
- Use Magic Wand for solid-color objects
- Use Brush for fine detail work

### 💡 Pro Tip: GPU Acceleration
Enable GPU acceleration in Advanced Settings for 3-5x faster processing (requires compatible graphics card).

---

Still have questions? Check the built-in help system (F1) or explore the comprehensive documentation in the docs/ folder! 🐼
