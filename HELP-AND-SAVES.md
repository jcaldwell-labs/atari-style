# Help System & Save Slots

## Overview
Two new quality-of-life features added to the screen saver:
1. **Help Modal** - Press 'H' to see parameter descriptions
2. **Save Slots** - Buttons 2-5 for saving/loading parameter presets

---

## Help System

### Activation
Press **H** on the keyboard to toggle the help modal on/off.

### What It Shows
- **Current animation name** in the title bar
- **4 parameter descriptions** with:
  - Parameter name
  - Description of what it controls
  - Valid range
  - Which joystick direction controls it

### Example Help Modal
```
┌────────────────────────────────────────────────────────┐
│           Fluid Lattice - Parameters                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  UP/DOWN: Rain Rate: Drop frequency (0-1.5)           │
│                                                        │
│  LEFT/RIGHT: Wave Speed: Propagation rate (0.05-1.0)  │
│                                                        │
│  UP-RIGHT/DOWN-LEFT: Drop Power: Impact (3-20)        │
│                                                        │
│  UP-LEFT/DOWN-RIGHT: Damping: Persistence (0.85-0.995)│
│                                                        │
│  Press H again to close                               │
│  BTN 2-5: Save/Load (Hold=Save, Tap=Load)            │
└────────────────────────────────────────────────────────┘
```

### Features
- ✅ Modal appears on top of animation (doesn't pause it)
- ✅ Blue background with bright cyan border
- ✅ Animation-specific information
- ✅ Shows joystick direction mappings
- ✅ Toggle on/off with same key

---

## Save Slot System

### Button Mapping
- **Button 2** → Slot [2]
- **Button 3** → Slot [3]
- **Button 4** → Slot [4]
- **Button 5** → Slot [5]

### How It Works

#### Save Parameters (Hold Button)
1. Adjust parameters to your liking with joystick
2. **Hold** a button (2-5) for 0.5 seconds or longer
3. See confirmation: "Saved to Slot X"
4. Slot indicator turns **green** at bottom of screen

#### Load Parameters (Quick Tap)
1. **Tap** a button (2-5) quickly (< 0.5 seconds)
2. If slot has save: parameters instantly restored
3. If slot empty: "Slot X empty" message
4. See confirmation: "Loaded Slot X"

### Visual Indicators

**Bottom of screen:**
```
Slots: [2] [3] [4] [5]
       ^^^  ^^^          Green = has save
            ^^^  ^^^     White = empty
```

**Feedback messages:**
- "Saved to Slot 2" (appears for 2 seconds)
- "Loaded Slot 3" (appears for 2 seconds)
- "Slot 4 empty" (appears for 2 seconds)

---

## Use Cases

### Preset Creation
1. Adjust Fluid Lattice for "rainstorm" effect
2. Hold Button 2 to save
3. Adjust for "calm pool" effect
4. Hold Button 3 to save
5. Now tap Button 2 or 3 to switch between presets!

### Animation Bookmarks
1. Find interesting Mandelbrot region
2. Zoom in and adjust detail
3. Hold Button 2 to bookmark
4. Explore elsewhere
5. Tap Button 2 to return instantly

### Quick Experiments
1. Start with default parameters
2. Make wild adjustments
3. If you like it, hold a button to save
4. If you don't, tap a saved slot to restore

### Cross-Animation Saves
Saves remember which animation they're from:
- Save Plasma settings to Slot 2
- Switch to Spirals
- Save Spiral settings to Slot 3
- Tap Slot 2 → switches back to Plasma with saved settings
- Tap Slot 3 → switches back to Spirals with saved settings

---

## Technical Details

### Hold Detection
- Button press time tracked on press
- Duration calculated on release
- **Threshold**: 0.5 seconds
- **< 0.5s** = Load
- **>= 0.5s** = Save

### Save Data Structure
```python
save_slot = {
    'animation_index': 5,  # Which animation
    'parameters': {
        'rain_rate': 0.8,
        'wave_speed': 0.2,
        'drop_strength': 12.0,
        'damping': 0.98
    }
}
```

### Feedback System
- Message displayed for 2 seconds
- Centered on screen
- Bright yellow color
- Non-intrusive

### Slot Persistence
- **In-memory only** - not saved to disk
- Resets when app closes
- Per-session presets
- 4 slots per session

---

## Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| H | Toggle help modal |
| Space | Next animation mode |
| ESC/Q | Exit to menu |

## Joystick Button Summary

| Button | Action |
|--------|--------|
| 0 | Next animation mode |
| 1 | Exit to menu |
| 2 | Save/Load Slot [2] |
| 3 | Save/Load Slot [3] |
| 4 | Save/Load Slot [4] |
| 5 | Save/Load Slot [5] |

---

## Tips

### Saving Best Practices
- Hold button firmly for full 0.5s
- Watch for "Saved to Slot X" confirmation
- Slot indicator turns green

### Loading Best Practices
- Tap button quickly
- Watch for "Loaded Slot X" confirmation
- If you see "empty", save to that slot first

### Help Usage
- Press H when you forget controls
- Help shows current animation's parameters
- Doesn't pause animation - see changes in real-time
- Press H again to close and regain screen space

### Creative Workflow
1. Open help (H) to see what you can control
2. Experiment with joystick
3. Find something cool → Save it
4. Keep experimenting
5. Load saved presets to compare
6. Build a collection of favorite settings

---

## Future Enhancements

Possible additions:
- Save to disk (persistent presets)
- Named presets (not just numbers)
- Export/import preset files
- More than 4 slots
- Preset sharing

---

## Testing Checklist

- [x] Help modal displays correctly
- [x] H key toggles help on/off
- [x] Parameter descriptions accurate
- [x] Joystick mappings shown
- [x] Save slot indicators visible
- [x] Hold button saves parameters
- [x] Quick tap loads parameters
- [x] Empty slot shows message
- [x] Feedback messages display
- [x] Cross-animation saves work
- [x] All 8 animations have help text

---

## Example Session

```
1. Launch screen saver (animation starts)
2. Press H → Help modal appears
3. See: "UP/DOWN: Rain Rate: Drop frequency (0-1.5)"
4. Close help (H again)
5. Push UP on joystick → More rain!
6. Push LEFT → Slower waves
7. Like this? Hold Button 2 for 0.5s
8. See: "Saved to Slot 2" (slot turns green)
9. Experiment more...
10. Want original back? Tap Button 2
11. See: "Loaded Slot 2" (instant restore!)
```

---

## Screen Layout

```
┌────────────────────────────────────────────────────────┐
│ Mode: Fluid Lattice       [Animation Rendering]  H: Help│
│ [6/8]                                             BTN0...│
│                                                          │
│ Rain Rate: 0.80          [Waves and ripples]            │
│ Wave Speed: 0.20                                        │
│ Drop Power: 12.0                                        │
│ Damping: 0.980                                          │
│                                                          │
│                      [Animation continues]              │
│                                                          │
│                  Loaded Slot 2  ← Feedback (2s)        │
│                                                          │
│ Slots: [2] [3] [4] [5]  ← Green if saved               │
│         ^^^ ^^^                                         │
└────────────────────────────────────────────────────────┘
```

---

## Ready to Use!

All features tested and working:
- ✅ Help system functional
- ✅ Save/load working
- ✅ Visual indicators clear
- ✅ Feedback messages display
- ✅ All 8 animations supported

**Run it**: `python run.py` → Select "Screen Saver" → Press H!
