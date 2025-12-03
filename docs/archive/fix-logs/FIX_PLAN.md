# Terminal Arcade - Usability Fix Plan

**Date**: 2025-01-18
**Critical Issue**: Terminal input conflicts causing crashes

---

## 🐛 **Root Cause**

**Problem**: All 4 new games call `term.inkey()` in their game loop AFTER InputHandler already called it in `get_input()`. This creates terminal state conflicts in fullscreen mode.

**Affected games**:
- ❌ Mandelbrot Explorer - crashes
- ❌ Oscilloscope Functions - crashes
- ❌ Spaceship Flying - crashes
- ❌ Target Shooter - crashes

**Working games** (don't call term.inkey()):
- ✅ Pac-Man
- ✅ Galaga
- ✅ Grand Prix
- ✅ Breakout
- ✅ All 4 demos/tools

---

## ✅ **Solution Options**

### **Option 1: Remove Custom Keyboard Handling** (RECOMMENDED)
Remove all `term.inkey()` calls from new games. Use only InputHandler.

**Pros**:
- Simple, proven pattern (works in 8 existing games)
- No terminal conflicts
- Guaranteed to work

**Cons**:
- Lose some features (TAB/SPACE toggle, letter keys)
- Need to map everything to InputType or joystick buttons

### **Option 2: Extend InputHandler**
Add new InputTypes to InputHandler for special keys (SPACE, TAB, letter keys).

**Pros**:
- Centralized input handling
- No game-level term.inkey() calls
- Cleaner architecture

**Cons**:
- Requires InputHandler changes
- More complex

### **Option 3: Single Shared Terminal**
Pass terminal object from InputHandler to games, ensure only one inkey() call.

**Pros**:
- Can keep custom keyboard handling
- Flexible

**Cons**:
- Complex to coordinate
- Easy to break

---

## 🎯 **Recommended Fix: Option 1**

**For each new game**:
1. Remove all `term.inkey()` calls
2. Use joystick buttons for mode toggle
3. Simplify to InputType-only handling
4. Match pattern from working games

**Example for Mandelbrot**:
```python
# OLD (broken):
def handle_input(self, input_type, raw_key):
    if raw_key:
        if raw_key == ' ':  # <-- Problem!
            self.parameter_mode = not self.parameter_mode

# NEW (working):
def handle_input(self, input_type):
    # Use Button 2 for mode toggle instead
    if input_type == InputType.SELECT:
        # Different behavior based on mode
        if self.parameter_mode:
            # Adjust selected parameter
        else:
            # Zoom in
```

---

## 🎮 **Simplified Control Scheme**

### **Universal Mapping** (All New Games)
```
Button 0 (A)     → Primary action / Select
Button 1 (B)     → Secondary action / Back
Button 2 (X)     → Toggle parameter mode
Button 3 (Y)     → Special action
Button 4         → Screenshot (where applicable)

Joystick         → Navigation (context-dependent)
Q key            → Exit (via InputType.QUIT)
ESC              → Exit (via InputType.BACK)
```

**No letter keys, no SPACE/TAB, no custom keyboard!**

---

## 📋 **Fix Checklist**

### **Mandelbrot Explorer**
- [ ] Remove `raw_key` parameter from handle_input()
- [ ] Remove all term.inkey() calls
- [ ] Map Button 2 to mode toggle
- [ ] Keep parameter mode, remove custom keys
- [ ] Test SPACE conflict removed

### **Oscilloscope Functions**
- [ ] Remove raw_key parameter
- [ ] Remove term.inkey() calls
- [ ] Map buttons for mode toggle
- [ ] Simplify input handling

### **Spaceship Flying**
- [ ] Remove raw_key parameter
- [ ] Remove term.inkey() calls
- [ ] Map buttons for controls
- [ ] Simplify input handling

### **Target Shooter**
- [ ] Remove raw_key parameter
- [ ] Remove term.inkey() calls
- [ ] Map buttons for shoot/adjust
- [ ] Simplify input handling

---

## 🧪 **Testing Framework**

### **Quick Test per Game**:
```python
# Test script
from terminal_arcade.games.GAME import run_GAME

print("Testing GAME...")
# Should run without crashes
# Exit with Q or ESC should work
# Basic controls should work
```

### **Acceptance Criteria**:
- ✅ Launches without crash
- ✅ Q key exits
- ✅ ESC exits
- ✅ Basic gameplay works
- ✅ No KeyboardInterrupt on exit

---

## 💡 **Pair Programming Session Format**

### **Session Structure**:

1. **You map out fixes** (5 min)
   - List specific changes for one game
   - Define button mappings
   - Expected behavior

2. **I implement** (10 min)
   - Make changes
   - Test import
   - Quick smoke test

3. **You test** (5 min)
   - Try the game
   - Report: works / broken / iterate

4. **Iterate** (repeat 2-3)
   - Fix issues found
   - Refine controls
   - Polish

5. **Move to next game**

### **Example Session for Mandelbrot**:

**You**: "Button 2 should toggle modes, remove SPACE key, make sure ESC exits"

**Me**: *implements changes, tests import*

**You**: "Testing... Button 2 works! But can't zoom out now"

**Me**: "Adding Button 1 for zoom out"

**You**: "Perfect! Move to next game"

---

## 🎯 **Immediate Action**

**Recommendation**:
1. Fix Mandelbrot first (most complex)
2. Use that pattern for other 3 games
3. Test each one
4. Commit working versions

**Alternative**:
- Schedule pair programming session
- Work through games one by one
- Get real-time feedback
- Iterate quickly

---

**What would you prefer?**
A. Let me fix all 4 games now (remove term.inkey(), simplify controls)
B. Pair programming session (you test as I implement)
C. Different approach?
