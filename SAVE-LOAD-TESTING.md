# Save/Load System Testing Guide

## Visual Indicators

### Slot Display (Bottom of Screen)
```
Slots: [2]     [3]     [4]     [5]
       ^^^     ^^^     ^^^     ^^^
       Color codes:
       - WHITE = Empty slot
       - BRIGHT_GREEN = Has saved parameters
       - BRIGHT_YELLOW = Currently pressing (not held long enough)
       - BRIGHT_RED = Holding 0.5s+ (about to save!)
```

### Progress Bar (While Holding)
```
Slots: [2]=   [3]     [4]     [5]
          ^^^
          Progress bar shows hold duration
          === means almost ready to save!
```

### Status Line (Row above slots)
```
BTN2:0.2s BTN3:0.4s  ← Shows which buttons are pressed and for how long
```

### Feedback Messages (Center, above slots)
```
Button 2 pressed...        ← When you press
Saved to Slot 2           ← After holding 0.5s
Loaded Slot 2             ← After quick tap
Slot 3 empty              ← If tapping empty slot
```

---

## Testing Procedure

### Step 1: Check Joystick Button Count
```bash
source venv/bin/activate
python test_save_buttons.py
```

**Expected**:
- Shows joystick name
- Shows total button count
- If < 6 buttons: Warning message
- Press each button to verify detection

**Your Joystick** (Trooper V2):
- Likely has 8 buttons (buttons 0-7)
- Buttons 2-5 should exist ✓

---

### Step 2: Visual Test in App

#### Launch App
```bash
python run.py
# Select "Screen Saver"
```

#### Test Button Press Detection
1. Look at bottom of screen: `Slots: [2] [3] [4] [5]` (all white)
2. Press Button 2 briefly
3. **Should see**:
   - Slot [2] turns YELLOW while pressed
   - Message: "Button 2 pressed..."
   - When released: "Loaded Slot 2" or "Slot 2 empty"

#### Test Hold Detection
1. Press and HOLD Button 2
2. **Should see**:
   - Slot [2] turns YELLOW
   - Progress bar appears: `[2]=`
   - Status shows: "BTN2:0.1s" (counting up)
   - After 0.5s: Slot turns RED
   - Progress bar fills: `[2]===`
   - When released: "Saved to Slot 2"
   - Slot turns GREEN (has save now)

#### Test Load
1. Adjust some parameters with joystick
2. Tap Button 2 quickly
3. **Should see**:
   - "Loaded Slot 2"
   - Parameters restore to saved values

---

### Step 3: Full Workflow Test

#### Save Different Configurations
1. Adjust parameters (e.g., push UP for more rain)
2. Hold Button 2 until it turns RED (0.5s)
3. Release → See "Saved to Slot 2", slot turns GREEN

4. Change parameters differently
5. Hold Button 3 until RED
6. Release → See "Saved to Slot 3", slot turns GREEN

#### Load Configurations
1. Tap Button 2 (quick press/release)
2. See "Loaded Slot 2", parameters change
3. Tap Button 3
4. See "Loaded Slot 3", parameters change back

#### Overwrite Save
1. Adjust parameters to new values
2. Hold Button 2 (the one already saved)
3. See progress bar → RED → "Saved to Slot 2"
4. Old save is now replaced

---

## Troubleshooting

### Problem: Buttons 2-5 Not Detected

**Check 1: Button Count**
```bash
python test_save_buttons.py
```
If shows "Warning: Only X buttons", your joystick doesn't have buttons 2-5.

**Solution Options**:
1. Use a joystick with more buttons
2. Modify code to use buttons 0,1,6,7 instead
3. Use keyboard fallback (we can add this)

---

### Problem: No Visual Feedback

**Check**: Look for these on screen:
- Bottom row: `Slots: [2] [3] [4] [5]`
- Legend: "Green=Saved Yellow=Pressing Red=Saving"
- Status line when pressing: `BTN2:0.3s`

If not visible, terminal might be too small.

**Solution**: Resize terminal to at least 80x24

---

### Problem: Hold Not Triggering

**Symptoms**:
- Press and hold but nothing happens
- Never turns RED
- No "Saved" message

**Debug**:
- Check status line shows: `BTN2:0.5s` or higher
- Make sure you're holding for full 0.5 seconds
- Try holding longer (1 second) to be sure

**Possible Issue**: Button released too early

---

### Problem: Load Always Says "Empty"

**Check**:
- Is slot GREEN? (has save)
- If WHITE, no save exists yet
- Must HOLD to save first, then TAP to load

---

## Expected Behavior Summary

### Slot Colors
| Color | Meaning |
|-------|---------|
| WHITE | Empty (no save) |
| YELLOW | Currently pressing (hold in progress) |
| RED | Held 0.5s+ (will save on release) |
| GREEN | Has saved parameters |

### Progress Indicators
| Indicator | Meaning |
|-----------|---------|
| `[2]` | Just the slot number |
| `[2]=` | Held ~0.2s (33% to save) |
| `[2]==` | Held ~0.3s (66% to save) |
| `[2]===` | Held 0.5s (ready to save!) |
| `BTN2:0.3s` | Status line showing hold time |

### Messages
- "Button X pressed..." = Initial press
- "Saved to Slot X" = Hold completed
- "Loaded Slot X" = Quick tap, restored params
- "Slot X empty" = Tried to load empty slot

---

## Debug Mode

The app now shows real-time debug info:
- **Status line**: Shows which buttons pressed and duration
- **Progress bars**: Visual countdown to 0.5s
- **Color changes**: Immediate visual feedback
- **Messages**: Confirm every action

---

## If Still Not Working

### Check These Files
1. `test_save_buttons.py` - Does it detect button presses?
2. Joystick button count - At least 6 buttons needed
3. Terminal size - At least 80 columns wide

### Common Issues
- **Joystick has only 4-5 buttons**: Buttons 2-5 don't exist
- **Wrong button numbering**: Joystick uses different ID scheme
- **Terminal too small**: Indicators off-screen

### Workaround
If your joystick doesn't have buttons 2-5, we can:
1. Remap to different buttons (e.g., 4,5,6,7)
2. Add keyboard shortcuts (2,3,4,5 keys)
3. Use a button combination (e.g., hold BTN1 + press BTN0)

**Let me know your joystick button count and I'll adjust!**

---

## Testing Checklist

- [ ] Run `test_save_buttons.py` - confirms button detection
- [ ] Launch screen saver - see slot indicators
- [ ] Press Button 2 - see YELLOW color
- [ ] Hold Button 2 - see progress bar `===`
- [ ] Hold 0.5s - see RED color
- [ ] Release - see "Saved to Slot 2"
- [ ] Slot turns GREEN
- [ ] Change parameters
- [ ] Tap Button 2 - see "Loaded Slot 2"
- [ ] Parameters restore

**If all checkmarks pass**: System working! ✓
**If any fail**: See troubleshooting section above
