# 🐼 Panda Mode Enhancement Guide

## Overview
Panda Mode makes texture sorting fun and engaging with interactive features, easter eggs, and dynamic tooltips!

## Features

### 1. Randomized Tooltip System
Get helpful (or hilarious) tooltips for every UI element:
- **21 UI actions** covered (sort, convert, settings, etc.)
- **6 normal variants** - Professional and helpful
- **6 vulgar variants** - Funny and edgy (opt-in only)
- **252 total tooltips** for variety

```python
from src.features.panda_mode import PandaMode

# Normal mode (default)
panda = PandaMode(vulgar_mode=False)
tooltip = panda.get_tooltip('sort_button')
# Returns: "Click to sort your textures into organized folders"

# Vulgar mode (opt-in)
panda_vulgar = PandaMode(vulgar_mode=True)
tooltip = panda_vulgar.get_tooltip('sort_button')
# Returns: "Click this to sort your damn textures. It's not rocket science, Karen."

# Override mode on-the-fly
tooltip = panda.get_tooltip('convert_button', mode='vulgar')
```

### 2. Panda Moods (13 States)
The panda reacts to your workflow:
- **HAPPY** 😊 - Ready to work
- **EXCITED** 🤩 - Something good happened
- **WORKING** 💼 - Processing files
- **TIRED** 😮‍💨 - Long session
- **CELEBRATING** 🎉 - Milestone reached
- **SLEEPING** 😴 - Taking a break
- **SARCASTIC** 🙄 - Slow progress detected
- **RAGE** 😡 - After 5 failures
- **DRUNK** 🥴 - After midnight usage
- **EXISTENTIAL** 🤔 - After 10,000+ files
- **MOTIVATING** 💪 - Encouraging user
- **TECH_SUPPORT** 🤓 - "Have you tried turning it off?"
- **SLEEPY** 🥱 - After 2 hours

```python
# Moods trigger automatically based on conditions
panda.track_operation_failure()  # After 5 failures → RAGE mode
panda.track_file_processed(path, size)  # After 10k files → EXISTENTIAL
panda.become_sleepy()  # After 2 hours → SLEEPY

# Get current mood indicator
emoji = panda.get_panda_mood_indicator()  # Returns: "😊"
```

### 3. Easter Eggs (24+ Triggers)
Discover hidden surprises:

| Trigger | Easter Egg |
|---------|------------|
| Click panda 10 times | Rage mode activation |
| Sort 1000 files | "HOLY SH*T!" achievement |
| Process at 3 AM | "Why are you awake?" |
| Cancel operation 5 times | "Make up your mind!" |
| Convert same file twice | "Really? Again?" |
| Click tabs quickly | Panda dance |
| Type "bamboo" | Bamboo mode |
| Type "ninja" | Stealth mode |
| Type "matrix" | Matrix mode |
| Press Konami code | Special achievement |
| Hover 30 seconds | Panda gets annoyed |
| Process 0 byte file | "Are you serious?" |
| Select same folder twice | "Déjà vu?" |
| Pet panda 50 times | Panda Whisperer achievement |
| ...and 10 more! | Keep exploring! |

```python
# Text-based easter eggs
panda.handle_text_input('bamboo')  # Triggers bamboo mode

# Konami code
konami = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
for key in konami:
    panda.track_konami_input(key)  # Triggers at end
```

### 4. Interactive Panda Pet
Interact with your panda companion:

```python
# Click the panda
response = panda.on_panda_click()
# Returns: "🐼 Hi there!" (varies each time)

# Hover over panda
thought = panda.on_panda_hover()
# Returns: "💭 Thinking about bamboo..."

# Right-click menu
menu = panda.on_panda_right_click()
# Returns: {'pet_panda': '🐼 Pet the panda', 'feed_bamboo': '🎋 Feed bamboo', ...}

# Pet the panda
reaction = panda.pet_panda_minigame()
# Returns: "🐼 *purrs like a cat* Wait, pandas don't purr..."
```

### 5. Smart Tracking
The panda learns from your behavior:

```python
# Track file operations
panda.track_file_processed('/path/to/file.png', file_size)

# Track failures (triggers rage after 5)
panda.track_operation_failure()

# Track cancellations (easter egg after 5)
panda.track_operation_cancel()

# Track folder selection (detects repeats)
panda.track_folder_selection('/path/to/folder')

# Track tab switching (detects rapid switching)
panda.track_tab_switch()

# Check time-based triggers
panda.check_3am_processing()  # Special message at 3 AM
panda.check_time_for_drunk_panda()  # After midnight
```

### 6. Statistics
Track everything:

```python
stats = panda.get_statistics()
# Returns:
# {
#     'enabled': True,
#     'vulgar_mode': False,
#     'current_mood': 'happy',
#     'facts_shown': 15,
#     'quotes_shown': 23,
#     'easter_eggs_triggered': 5,
#     'easter_eggs_list': ['bamboo', 'konami', ...],
#     'files_processed': 1234,
#     'click_count': 8,
#     'failed_operations': 2,
#     'operation_cancellations': 1,
#     'panda_pet_count': 12,
#     'elapsed_time_seconds': 3600.0,
#     'elapsed_time_hours': 1.0,
# }
```

## Usage Examples

### Basic Setup
```python
from src.features.panda_mode import PandaMode

# Create panda (vulgar mode off by default)
panda = PandaMode(vulgar_mode=False)

# Enable vulgar mode later
panda.set_vulgar_mode(True)
```

### Integration in UI
```python
# Get tooltip for button
tooltip = panda.get_tooltip('sort_button')
button.setToolTip(tooltip)

# Update on hover
def on_hover():
    thought = panda.on_panda_hover()
    status_bar.showMessage(thought)

# Handle click
def on_panda_clicked():
    response = panda.on_panda_click()
    show_notification(response)

# Track operations
def process_file(path, size):
    try:
        # ... process file ...
        panda.track_file_processed(path, size)
    except Exception:
        panda.track_operation_failure()
```

### Easter Egg Detection
```python
# Text input handler
def on_text_entered(text):
    if panda.handle_text_input(text):
        show_easter_egg_notification()

# Operation patterns
def on_cancel():
    panda.track_operation_cancel()
    # Automatically triggers easter egg after 5 cancels

# Time-based checks
import schedule
schedule.every().hour.do(panda.check_3am_processing)
schedule.every().hour.do(panda.become_sleepy)
```

## Special Behaviors

### Rage Mode
Triggered automatically after 5 failed operations:
```python
# Automatic trigger
for i in range(5):
    panda.track_operation_failure()
# → Panda enters RAGE mode with angry animation
```

### Existential Crisis
After processing 10,000+ files:
```python
# Processes trigger automatically
for i in range(10000):
    panda.track_file_processed(f'/file_{i}.png', 1024)
# → "What is the meaning of sorting textures? 🌌"
```

### Drunk Panda
Random chance after midnight:
```python
if panda.check_time_for_drunk_panda():
    # 30% chance between 0-5 AM
    # → "Heyyy... you're pretty cool, you know that? 🍺"
```

## Tips & Tricks

1. **Tooltip Variety**: Call `get_tooltip()` each time you show a tooltip for maximum variety
2. **Easter Egg Hunting**: Try typing game references, coding terms, and memes
3. **Panda Stats**: Check statistics regularly to track progress
4. **Mood Watching**: The panda's mood reflects your workflow - use it as feedback
5. **Pet Rewards**: Pet the panda regularly for morale boosts (yours and the panda's!)

## Demo Script

Run the included demo to see all features:
```bash
python panda_mode_demo.py
```

This will demonstrate:
- All tooltip variations
- All mood states
- Easter egg triggers
- Interactive features
- Tracking system
- Special behaviors
- ASCII animations

## Configuration

### Disable Panda Mode
```python
panda.disable()  # Turns off all panda features
panda.enable()   # Re-enables
```

### Toggle Vulgar Mode
```python
panda.set_vulgar_mode(True)   # Enable
panda.set_vulgar_mode(False)  # Disable (default)
```

### Reset Statistics
```python
panda.reset_statistics()  # Clears all counters and tracking
```

## API Reference

### Main Methods
- `get_tooltip(action, mode=None)` - Get random tooltip for UI element
- `on_panda_click()` - Handle panda click
- `on_panda_hover()` - Get panda thought
- `on_panda_right_click()` - Get context menu
- `get_panda_mood_indicator()` - Get mood emoji
- `pet_panda_minigame()` - Pet the panda

### Tracking Methods
- `track_file_processed(path, size)` - Track file operation
- `track_operation_failure()` - Track failed operation
- `track_operation_cancel()` - Track cancelled operation
- `track_folder_selection(path)` - Track folder selection
- `track_tab_switch()` - Track tab switching
- `track_konami_input(key)` - Track Konami code

### Mood Methods
- `trigger_rage_mode()` - Enter rage mode
- `existential_crisis()` - Enter existential mode
- `become_sleepy()` - Enter sleepy mode
- `become_sarcastic()` - Enter sarcastic mode
- `motivate_user()` - Get motivational quote
- `get_random_tech_support_quote()` - Get tech support quote

### Utility Methods
- `get_statistics()` - Get comprehensive stats
- `reset_statistics()` - Reset all counters
- `set_vulgar_mode(enabled)` - Toggle vulgar mode
- `enable()` / `disable()` - Toggle panda mode

## Backward Compatibility

All new features are:
- ✅ **Optional** - Vulgar mode off by default
- ✅ **Non-breaking** - Existing code continues to work
- ✅ **Additive** - Only adds new methods, doesn't modify existing ones
- ✅ **Safe** - No side effects unless explicitly called

## Support

For issues or feature requests:
1. Check the demo script for usage examples
2. Review the comprehensive docstrings in the code
3. File an issue on GitHub

---

**Made with 🎋 by a panda who really loves bamboo and texture sorting**
