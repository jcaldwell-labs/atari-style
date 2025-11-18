# Mandelbrot Explorer - Dual-Mode UI Redesign

**Date**: 2025-01-18
**Status**: Complete UI Overhaul

---

## 🎯 **Major UI Redesign**

Completely redesigned the Mandelbrot Explorer with:
- ✅ Professional parameter panel using `/usr/bin/boxes`
- ✅ Dual-mode joystick control (Pan/Zoom vs Parameter Adjust)
- ✅ TAB key to toggle between modes
- ✅ Clean, intuitive interface
- ✅ Fixed all keyboard mapping issues

---

## 📦 **New Parameter Panel** (Top-Right)

Uses `/usr/bin/boxes -d dog -a c` to create a beautiful bordered panel:

```
    __   _,--="=--,_   __
  /  \."    .-.    "./  \
 /  ,/  _   : :   _  \/` \
 \  `| /o\  :_:  /o\ |\__/
  `-'| :="~` _ `~"=: |
     \`     (_)     `/
  .-'  ,'| .-. |\  `-.
 /      / \.-./ \  jgs\
 \    _/\     /\_    /
  `--'   `~-~'   `--'

MANDELBROT PARAMETERS

MODE: PAN/ZOOM

  Palette: electric
  Iterations: 50
  Color Cycle: OFF
  Cycle Speed: 0.10
  Show Coords: ON

Center: (-0.500000, 0.000000i)
Zoom: 1.500000e+00

    __________________
```

**Dog box style** creates fun ASCII art borders!

---

## 🎮 **Dual-Mode System**

### **Mode 1: PAN/ZOOM** (Default)
```
Joystick     →  Pan the fractal view
Button 0     →  Zoom IN
Button 1     →  Zoom OUT
```

Bottom hint: `[TAB] Parameter Mode | USE JOYSTICK: Pan & Zoom` (CYAN)

### **Mode 2: PARAMETER ADJUST**
```
Joystick ↕   →  Select parameter (up/down)
Joystick ← → →  Adjust value (left/right)
Button 0     →  Toggle boolean params
```

Bottom hint: `[TAB] Pan/Zoom Mode | USE JOYSTICK: ↕ Select Param, ← → Adjust Value` (GREEN)

### **Toggle Between Modes**
```
TAB key      →  Switch mode (instantly!)
```

---

## 📊 **5 Adjustable Parameters**

When in **Parameter Mode**, joystick navigates these settings:

### **1. Palette** (8 options)
- electric, fire, ocean, sunset, forest, psychedelic, copper, grayscale
- **Left/Right**: Cycle through palettes
- **Selected**: Shows `► Palette: electric`

### **2. Iterations** (10-1000)
- Controls fractal detail level
- **Left/Right**: Adjust by ±10
- Range: 10 → 1000

### **3. Color Cycle** (ON/OFF)
- Toggle automatic color animation
- **Left/Right or Button0**: Toggle
- Creates flowing color effects

### **4. Cycle Speed** (0.05-1.0)
- How fast colors cycle
- **Left/Right**: Adjust by ±0.05
- 0.05 = very slow, 1.0 = very fast

### **5. Show Coords** (ON/OFF)
- Toggle coordinate display
- **Left/Right or Button0**: Toggle

---

## 🎨 **Visual Indicators**

### **Parameter Panel Colors**
- **Bright Cyan** = "MODE: PAN/ZOOM"
- **Bright Green** = "MODE: PARAMETER ADJUST"
- **Bright Yellow** = `► Selected parameter`
- **White** = Normal parameters

### **Bottom Bar**
- **Bright Cyan** = Pan/Zoom mode active
- **Bright Green** = Parameter mode active

**You always know which mode you're in!**

---

## 🎮 **Complete Controls**

### **Mode Toggle**
```
TAB          →  Switch between Pan/Zoom and Parameter modes
```

### **Pan/Zoom Mode** (Default)
```
JOYSTICK:
  Stick      →  Pan view
  Button 0   →  Zoom IN
  Button 1   →  Zoom OUT
  Button 4   →  Screenshot

KEYBOARD:
  Arrow/WASD →  Pan
  Z          →  Zoom IN
  X          →  Zoom OUT
  S          →  Screenshot
```

### **Parameter Mode**
```
JOYSTICK:
  Stick ↕    →  Select parameter (up/down)
  Stick ← →  →  Adjust value (left/right)
  Button 0   →  Toggle (for ON/OFF params)
  Button 4   →  Screenshot

KEYBOARD:
  (All parameters shown in panel)
  S          →  Screenshot
```

### **Always Available**
```
1-6          →  Jump to bookmarks
H            →  Toggle help
R            →  Reset to overview
ESC/Q        →  Exit to menu
```

---

## 🔧 **How Parameter Mode Works**

### **Example: Changing Palette**

1. Press **TAB** → Enter parameter mode
2. Look at panel → See `MODE: PARAMETER ADJUST` (green)
3. Joystick UP/DOWN → Move to `► Palette: electric`
4. Joystick LEFT/RIGHT → Cycle through palettes
5. Watch fractal colors change in real-time!
6. Press **TAB** → Return to pan/zoom mode

### **Example: Enabling Color Cycling**

1. Press **TAB** → Parameter mode
2. Joystick DOWN → Navigate to `► Color Cycle: OFF`
3. Joystick RIGHT (or Button 0) → Toggle to ON
4. Watch colors animate!
5. Navigate to `► Cycle Speed: 0.10`
6. Joystick RIGHT → Increase speed (0.15, 0.20, etc.)
7. Press **TAB** → Back to exploration

---

## 📸 **Screenshot Location**

Screenshots save to:
```
~/.terminal-arcade/mandelbrot-screenshots/
```

To find your screenshots:
```bash
# List all
ls ~/.terminal-arcade/mandelbrot-screenshots/

# View most recent
cat ~/.terminal-arcade/mandelbrot-screenshots/mandelbrot_*.txt | tail -100

# Open in editor
nano ~/.terminal-arcade/mandelbrot-screenshots/mandelbrot_20251118_*.txt
```

Each screenshot includes:
- The fractal image (ASCII art)
- Metadata box (top-right) with coordinates, zoom, palette, iterations

---

## 🎯 **Why This Design Works**

### **Problems Solved**
1. ✅ **Button 1 conflict** - Now only zooms in pan/zoom mode
2. ✅ **Keyboard mapping confusion** - Simplified to TAB toggle
3. ✅ **Hidden features** - All parameters visible in panel
4. ✅ **Mode confusion** - Clear visual indicators

### **UX Improvements**
- **Single toggle** (TAB) instead of many keys
- **Visual parameter editor** instead of memorizing keys
- **Real-time feedback** in parameter box
- **Mode-aware controls** - joystick behaves differently per mode
- **Professional look** with boxes ASCII art

---

## 📊 **Implementation Details**

### **Files Modified**
- `terminal_arcade/games/mandelbrot/game.py`

### **New Code**
- Lines 95-104: Parameter mode variables and parameter list
- Lines 210-279: Parameter sync and box creation with `/usr/bin/boxes`
- Lines 281-312: New draw_ui with parameter panel
- Lines 443-479: `_adjust_parameter()` method for value changes
- Lines 481-533: Dual-mode input handling

**Total additions**: ~200 lines

---

## 🧪 **Testing Guide**

### **Test Parameter Panel**
1. Launch Mandelbrot Explorer
2. Look at **top-right** → See parameter box with dog border
3. ✅ Should show all 5 parameters
4. ✅ Should show current mode
5. ✅ Should show coordinates

### **Test Mode Toggle**
1. Press **TAB**
2. ✅ Panel changes: `MODE: PAN/ZOOM` → `MODE: PARAMETER ADJUST`
3. ✅ Bottom bar changes color: Cyan → Green
4. ✅ First parameter shows `►` indicator

### **Test Parameter Navigation** (Joystick)
1. In parameter mode
2. **Joystick UP/DOWN** → Move `►` through parameters
3. ✅ Selector moves through all 5 params

### **Test Parameter Adjustment** (Joystick)
1. Select "Palette" parameter
2. **Joystick LEFT/RIGHT** → Cycle palettes
3. ✅ Fractal colors change immediately
4. ✅ Panel updates to show new palette name

### **Test Pan/Zoom Mode**
1. Press **TAB** to return to pan/zoom
2. **Joystick** → Pan view
3. **Button 0** → Zoom in
4. **Button 1** → Zoom out
5. ✅ All work as expected

### **Test Exit**
1. Press **ESC** or **Q**
2. ✅ Exits cleanly to menu

---

## 🎨 **Boxes Styles Available**

Current: **dog** (playful ASCII art dog)

Other options you can try (edit line 259 in game.py):
- `stone` - Stone block border
- `cat` - ASCII art cat
- `peek` - Peeking eyes
- `scroll` - Scroll/parchment
- `columns` - Greek columns
- `simple` - Simple box drawing chars

---

## 💡 **Usage Workflow**

### **Quick Exploration**
```
1. Stay in Pan/Zoom mode (default)
2. Use joystick to navigate
3. Button 0 to zoom in
4. Button 1 to zoom out
5. Button 4 to screenshot
```

### **Detailed Customization**
```
1. Press TAB → Parameter mode
2. Joystick ↕ → Select setting
3. Joystick ← → → Adjust
4. Press TAB → Back to exploring
```

---

## 📈 **Comparison**

| Aspect | Old Design | New Design |
|--------|-----------|------------|
| Parameter visibility | Hidden | ✅ Always visible in panel |
| Mode indication | None | ✅ Color-coded panel + bottom bar |
| Joystick function | Single purpose | ✅ Dual mode (TAB toggle) |
| Parameter adjustment | Keyboard only | ✅ Joystick navigation |
| Box borders | Simple ╔═╗ | ✅ ASCII art (dog style) |
| Controls confusion | Many keys | ✅ One toggle (TAB) |

---

## 🚀 **Result**

The Mandelbrot Explorer now has a **professional, intuitive interface**:

- ✅ Beautiful parameter panel (dog box)
- ✅ Dual-mode joystick (TAB to toggle)
- ✅ All settings visible and adjustable
- ✅ Clear mode indicators
- ✅ No keyboard mapping confusion
- ✅ Real-time parameter updates

**Much more user-friendly!** 🎨

---

**Test it out - press TAB to toggle modes!**
