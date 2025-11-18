# Terminal Arcade - Universal Control Scheme Standard

**Version**: 1.0
**Date**: 2025-01-18
**Status**: Official Standard

---

## 🎯 **Design Principles**

1. **Consistency**: Same buttons do similar things across all games
2. **Intuitive**: Button meanings are obvious
3. **No conflicts**: Never use Button 1 for exit
4. **Mode-aware**: Controls adapt to current mode
5. **Keyboard fallback**: Arrow keys always work

---

## 🎮 **Universal Button Assignments**

### **Global (All Games)**
```
ESC key       → Exit to menu (ALWAYS)
Q key         → Exit to menu (ALWAYS)
Button 1      → NEVER used for exit (anti-pattern!)
```

### **Standard Arcade Games** (No dual-mode)
```
Joystick      → Navigate / Move
Button 0      → Primary action (Fire, Jump, Select)
Button 1      → Secondary action (Brake, Special, Back to menu context only)
Arrow/WASD    → Same as joystick
```

### **Dual-Mode Games** (Parameter adjustment support)
```
Button 2      → Toggle mode (Game ↔ Parameter adjust)
Button 3      → Context help / Info
Button 4      → Screenshot / Special feature

Joystick behavior changes based on mode:
  - Game mode: Navigate, aim, fly, etc.
  - Parameter mode: UP/DOWN=select, LEFT/RIGHT=adjust
```

---

## 📋 **Mode Pattern for Dual-Mode Games**

### **Game Mode** (Default - Cyan indicators)
```
Joystick      → Game-specific navigation
Button 0      → Primary game action
Button 1      → Secondary game action
Button 2      → Enter parameter mode
ESC/Q         → Exit
```

### **Parameter Mode** (Green indicators)
```
Joystick ↕    → Select parameter (shows ► indicator)
Joystick ← →  → Adjust selected parameter value
Button 0      → Quick adjust / Toggle
Button 1      → (reserved / unused)
Button 2      → Return to game mode
ESC/Q         → Exit
```

---

## 🚫 **Anti-Patterns** (DO NOT USE)

### **❌ Button 1 for Exit**
**Problem**: Confusing, conflicts with secondary actions
**Solution**: Use ESC/Q only

### **❌ SPACE/TAB for mode toggle**
**Problem**: Terminal input conflicts in fullscreen
**Solution**: Use Button 2

### **❌ Custom term.inkey() calls**
**Problem**: Conflicts with InputHandler, causes crashes
**Solution**: Use only InputHandler.get_input()

### **❌ Letter keys for critical functions**
**Problem**: Not accessible without keyboard
**Solution**: Map to buttons

---

## ✅ **Standard Game Implementations**

### **Classic Arcade** (Pac-Man, Galaga, Grand Prix, Breakout)
```python
def handle_input(self, input_type):
    if input_type == InputType.QUIT or input_type == InputType.BACK:
        self.running = False
    elif input_type == InputType.UP:
        # Move up
    elif input_type == InputType.SELECT:
        # Primary action
    # ... etc
```

**No buttons needed beyond InputType!**

### **Dual-Mode Games** (Mandelbrot, Oscilloscope, Spaceship, Target Shooter)
```python
def handle_input(self, input_type):
    # Exit
    if input_type == InputType.QUIT or input_type == InputType.BACK:
        self.running = False
        return

    # Check buttons
    if self.input_handler.joystick_initialized:
        buttons = self.input_handler.get_joystick_buttons()

        # Button 2 = Mode toggle
        if buttons.get(2, False):
            self.parameter_mode = not self.parameter_mode
            time.sleep(0.2)  # Debounce
            return

    # Parameter mode
    if self.parameter_mode:
        if input_type == InputType.UP:
            # Select previous param
        elif input_type == InputType.LEFT:
            # Decrease value
        # ...

    # Game mode
    else:
        if input_type == InputType.UP:
            # Game-specific action
        # ...
```

---

## 🎨 **UI Indicators**

### **Mode Display** (Required for dual-mode games)
```
Parameter panel (top or bottom corner):
╔═══════════════════╗
║ GAME PARAMETERS   ║
║                   ║
║ MODE: GAME        ║  ← CYAN when in game mode
║ MODE: ADJUST      ║  ← GREEN when in parameter mode
║                   ║
║ ► Param: value    ║  ← YELLOW for selected
║   Other: value    ║  ← WHITE for others
╚═══════════════════╝
```

### **Bottom Hint Bar**
```
Cyan:  "BTN2=Adjust Mode | JOYSTICK: Game Controls | ESC=Exit"
Green: "BTN2=Game Mode | JOYSTICK: ↕ Select, ← → Adjust | ESC=Exit"
```

---

## 📖 **Control Documentation Template**

Each game should document:

### **Game Name**
**Primary Controls**:
- Joystick: [What it does in game mode]
- Button 0: [Primary action]
- Button 1: [Secondary action]

**If dual-mode**:
- Button 2: Toggle parameter mode
- In parameter mode: Joystick ↕ selects, ← → adjusts

**Universal**:
- ESC/Q: Exit to menu

---

## 🎯 **Implementation Checklist**

For each game:
- [ ] No custom `term.inkey()` calls
- [ ] Button 1 NOT used for exit
- [ ] ESC/Q exit via InputType.QUIT/BACK
- [ ] If dual-mode: Button 2 toggles
- [ ] If dual-mode: Color-coded UI (Cyan/Green)
- [ ] If dual-mode: Parameter panel with ► indicator
- [ ] Bottom hint bar shows current mode
- [ ] Debounce on button toggles (0.2s)

---

## 💡 **Why This Standard Matters**

### **User Experience**
- Predictable controls across all games
- Button 2 always means "settings/adjust"
- ESC always means "exit"
- No surprises, no conflicts

### **Developer Experience**
- Clear pattern to follow
- Proven input handling
- No terminal state issues
- Easy to extend

### **Maintainability**
- Consistent codebase
- Easy to debug
- Simple to document

---

## 🚀 **Rollout Plan**

### **Phase 1: Core Fix** ✅ DONE
- Remove term.inkey() from all 4 new games
- Map Button 2 to mode toggle
- Ensure ESC/Q work

### **Phase 2: Refinement** (Next)
- Remove any remaining Button 1 exit mappings
- Add button legends to help screens
- Test each game's control feel
- Adjust button mappings based on feedback

### **Phase 3: Polish**
- Create per-game control cards
- Add visual button indicators
- In-game button tutorials
- Consistent help overlay format

---

## 📝 **Button Reference Card**

```
╔══════════════════════════════════════╗
║  TERMINAL ARCADE BUTTON REFERENCE    ║
╠══════════════════════════════════════╣
║  Button 0   Primary Action / Select  ║
║  Button 1   Secondary / Game Action  ║
║  Button 2   Parameter Mode Toggle    ║
║  Button 3   Help / Info              ║
║  Button 4   Screenshot / Special     ║
║                                      ║
║  ESC / Q    Exit to Menu (ALWAYS)    ║
╚══════════════════════════════════════╝
```

---

## ✅ **Next Steps**

1. **Fix math import** ✅ Done
2. **Test all 12 games**
3. **Remove Button 1 exit everywhere**
4. **Refine button feel**
5. **Document final controls**

---

**Standard established! All games should follow this pattern.** 🎮
