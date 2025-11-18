# Controls Reference

## Joystick Mapping Utilities

If you want to use your joystick with other terminal applications or customize button mappings beyond what's built-in:

### qjoypad
A popular Linux utility that maps joystick buttons to keyboard and mouse actions, allowing you to control any application, including terminal programs.

```bash
# Install on Debian/Ubuntu
sudo apt install qjoypad

# Launch GUI
qjoypad
```

### antimicrox
A graphical application that lets you map joystick buttons to keyboard presses or mouse movements, making it easy to use a controller for games or terminal tasks.

```bash
# Install on Debian/Ubuntu
sudo apt install antimicrox

# Launch GUI
antimicrox
```

**Note**: These utilities work system-wide and can override the built-in joystick controls in this application. Disable them if you want to use the native joystick support.

---

## Keyboard Controls (All Demos)

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Navigate / Move |
| Enter / Space | Select / Action |
| ESC / Q | Back / Exit |
| X | Quit (alternative) |

## Joystick Button Mapping

### Navigation Contexts

**Menu:**
| Button | Action | Notes |
|--------|--------|-------|
| Button 0 | Select / Action | Usually A button (Xbox) or Cross (PS) |
| Button 1 | Back / Exit | Usually B button (Xbox) or Circle (PS) |
| Analog Stick | Navigate | Up/Down to select menu items |

**Starfield:**
| Button | Action | Notes |
|--------|--------|-------|
| Button 0 | Toggle Color Mode | Cycles through 3 color modes |
| Button 1 | Exit to Menu | Returns to main menu |
| Analog Stick Y-axis | Control Warp Speed | Up/Down adjusts speed |

**Screen Saver:**
| Button | Action | Notes |
|--------|--------|-------|
| Button 0 | Next Animation Mode | Cycles through 4 animations |
| Button 1 | Exit to Menu | Returns to main menu |
| Analog Stick (All 8 dirs) | Adjust Parameters | See opposite pairs below |

### Joystick Test (Special Case)

**In the Joystick Test demo, ALL buttons can be tested freely:**

- **Button 0-7**: No action assigned - press to see visual feedback
- **Analog Sticks**: Move to see crosshair position
- **Exit**: Use **KEYBOARD** ESC or Q only

> **Why?** The joystick test is designed to let you test every button without triggering navigation. This is the only demo where joystick buttons don't perform actions.

## Demo-Specific Controls

### Starfield
- **Up/Down or Joystick Y-axis**: Increase/decrease warp speed
- **Left/Right**: Fine speed adjustment
- **Space or Button 0**: Toggle color mode (Monochrome → Rainbow → Speed-based)
- **ESC/Q or Button 1**: Exit to menu

### Screen Saver
- **Space or Button 0**: Next animation mode
- **ESC/Q or Button 1**: Exit to menu

**Joystick Directional Controls** (Opposite directions control same parameter):

**Pair 1: UP ↔ DOWN** → Parameter 1
- **↑ (Up)**: Increase Parameter 1
- **↓ (Down)**: Decrease Parameter 1

**Pair 2: RIGHT ↔ LEFT** → Parameter 2
- **→ (Right)**: Increase Parameter 2
- **← (Left)**: Decrease Parameter 2

**Pair 3: UP-RIGHT ↔ DOWN-LEFT** → Parameter 3
- **↗ (Up-Right)**: Increase Parameter 3
- **↙ (Down-Left)**: Decrease Parameter 3

**Pair 4: UP-LEFT ↔ DOWN-RIGHT** → Parameter 4
- **↖ (Up-Left)**: Increase Parameter 4
- **↘ (Down-Right)**: Decrease Parameter 4

**Animation Modes** (8 total, each with 4 adjustable parameters):

1. **Lissajous Curve**
   - Param 1: Frequency X (1-10)
   - Param 2: Frequency Y (1-10)
   - Param 3: Phase offset (0-2π)
   - Param 4: Resolution/Points (100-1000)

2. **Spiral**
   - Param 1: Number of spirals (1-8)
   - Param 2: Rotation speed (0.1-5.0x)
   - Param 3: Tightness (2-15)
   - Param 4: Scale/Size (0.2-0.8)

3. **Wave Circles**
   - Param 1: Number of circles (5-30)
   - Param 2: Wave amplitude (0.5-8.0)
   - Param 3: Wave frequency (0.1-2.0)
   - Param 4: Circle spacing (1-6)

4. **Plasma**
   - Param 1: X frequency (0.01-0.3)
   - Param 2: Y frequency (0.01-0.3)
   - Param 3: Diagonal frequency (0.01-0.3)
   - Param 4: Radial frequency (0.01-0.3)

5. **Mandelbrot Zoomer**
   - Param 1: Zoom level (0.1-1000x)
   - Param 2: Center X (-2.0 to 1.0)
   - Param 3: Center Y (-1.5 to 1.5)
   - Param 4: Detail/Iterations (10-200)

6. **Fluid Lattice**
   - Param 1: Wave speed (0.1-2.0)
   - Param 2: Damping factor (0.8-0.99)
   - Param 3: Rain drop rate (0.0-1.0)
   - Param 4: Drop impact strength (1-15)

7. **Particle Swarm**
   - Param 1: Number of particles (10-100)
   - Param 2: Movement speed (0.5-5.0)
   - Param 3: Cohesion/attraction (0.0-2.0)
   - Param 4: Separation/repulsion (0.0-3.0)

8. **Tunnel Vision**
   - Param 1: Depth speed (0.1-5.0)
   - Param 2: Rotation speed (-2.0 to 2.0)
   - Param 3: Tunnel size (0.3-3.0)
   - Param 4: Color cycle speed (0.1-3.0)

**Performance**: Runs at ~60 FPS with 2x animation speed multiplier

### Joystick Test
- **Joystick**: Move to see crosshair tracking
- **All Buttons**: Press to see button state indicators
- **KEYBOARD ESC/Q**: Exit (joystick buttons don't exit)

## Button Debouncing

All button and key presses are debounced to prevent accidental double-triggers:
- Joystick buttons only trigger on **new press** (not held)
- Menu navigation has 150ms debounce delay
- Action buttons have 200ms debounce delay
