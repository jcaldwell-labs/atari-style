# Joystick Control Patterns

Shared joystick control conventions for atari-style and related projects.

## Standard Controller Mapping

```
              ┌─────────────────────────────────────────────────────────┐
              │                    CONTROLLER LAYOUT                     │
              ├─────────────────────────────────────────────────────────┤
              │                                                         │
              │           [LB/L1]                    [RB/R1]            │
              │           [LT/L2]                    [RT/R2]            │
              │                                                         │
              │    ┌───┐                                  (Y)           │
              │    │ ↑ │                               (X) (B)          │
              │   ┌┴───┴┐   [BACK]  [START]             (A)            │
              │   │←   →│                                               │
              │   └┬───┬┘                                               │
              │    │ ↓ │     ┌───┐        ┌───┐                        │
              │    └───┘     │ L │        │ R │                        │
              │   D-PAD      └───┘        └───┘                        │
              │            LEFT STICK   RIGHT STICK                     │
              └─────────────────────────────────────────────────────────┘
```

## Button Mapping by Application

| Button | ID | Menu/Navigation | Games | GPU Shaders | Visualizers |
|--------|:--:|-----------------|-------|-------------|-------------|
| A/Cross | 0 | Select/Confirm | Fire/Action | Cycle Color | Toggle Mode |
| B/Circle | 1 | Back/Cancel | Secondary | Save Preset | Back |
| X/Square | 2 | - | Tertiary | Load Preset | - |
| Y/Triangle | 3 | Help/Toggle | Pause | Reset Params | Help |
| LB/L1 | 4 | Page Up | - | Prev Slot | - |
| RB/R1 | 5 | Page Down | - | Next Slot | - |
| Back/Select | 6 | - | - | Toggle HUD | - |
| Start | 7 | - | Pause | Pause | - |

## Analog Stick Usage

### Left Stick (Primary)
- **Navigation**: Move through menus, control characters
- **Parameter Control**: Params 0-1 in shader controller
- **Normalized Range**: -1.0 to 1.0 per axis
- **Deadzone**: 0.15 (15% center dead zone)

### Right Stick (Secondary)
- **Parameter Control**: Params 2-3 in shader controller
- **Camera/Zoom**: Secondary navigation in viewers
- **Axes**: Usually mapped to axes 2-3 or 4-5

### D-Pad
- **Menu Navigation**: Discrete up/down/left/right
- **Mode Switching**: Cycle through shaders/modes
- **HAT Input**: Read via `joystick.get_hat(0)`

## Implementation Details

### Deadzone Handling

```python
# Standard deadzone implementation
deadzone = 0.15
x = joystick.get_axis(0)
x = x if abs(x) > deadzone else 0.0
```

### Button Edge Detection

Only trigger on button press, not hold:

```python
# Track previous state
current = joystick.get_button(btn_id)
was_pressed = previous_buttons.get(btn_id, False)

if current and not was_pressed:  # Rising edge
    handle_button_press(btn_id)

previous_buttons[btn_id] = current
```

### Health Checks

The input handler includes automatic health monitoring:
- Periodic device checks (every 1 second)
- Automatic reconnection attempts (every ~30 frames)
- Graceful fallback to keyboard when disconnected
- Signal handlers for clean USB device release

## Project-Specific Controls

### Games (pacman, galaga, etc.)

| Control | Action |
|---------|--------|
| Left Stick | Movement (digital threshold: 0.5) |
| Button 0 | Fire / Select |
| Button 1 | Back / Cancel |
| ESC / Q | Quit to menu |

### Screen Saver

| Control | Action |
|---------|--------|
| Left Stick X | Parameter 1 (e.g., speed) |
| Left Stick Y | Parameter 2 (e.g., density) |
| Right Stick X | Parameter 3 |
| Right Stick Y | Parameter 4 |
| D-Pad | Switch animation mode |
| Buttons 1-3 | Load saved presets |
| Button 0 | Save current preset |

### GPU Shader Controller

| Control | Action |
|---------|--------|
| Left Stick | Params 0-1 (normalized 0-1) |
| Right Stick | Params 2-3 (normalized 0-1) |
| A/Button 0 | Cycle color mode (0-3) |
| B/Button 1 | Save to preset slot |
| X/Button 2 | Load from preset slot |
| Y/Button 3 | Reset to defaults |
| LB/RB | Cycle preset slot (0-3) |
| D-Pad L/R | Switch composite shader |
| Back | Toggle HUD overlay |
| Start | Pause animation |

## Keyboard Fallback

All joystick controls have keyboard equivalents:

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Navigation |
| Enter / Space | Select |
| ESC / Q | Back / Quit |
| H | Toggle help/HUD |
| C | Cycle mode |
| R | Reset |

## Troubleshooting

### Joystick Not Detected

1. Check USB connection
2. Verify with `joystick_test.py`:
   ```bash
   python -c "from atari_style.demos.joystick_test import run_joystick_test; run_joystick_test()"
   ```
3. WSL users: Ensure usbipd has attached the device

### Axis Drift

- Increase deadzone if experiencing drift
- Default 0.15 works for most controllers
- Modify in `input_handler.py` if needed

### Button Mapping Wrong

Different controllers map buttons differently:
- Xbox: A=0, B=1, X=2, Y=3
- PlayStation: Cross=0, Circle=1, Square=2, Triangle=3
- Use `joystick_test.py` to verify your controller's mapping

### USB Device Lockup (WSL)

If joystick causes system freeze:
1. Ctrl+C should trigger emergency cleanup
2. If frozen, detach USB device from host
3. The input handler includes signal handlers for safe cleanup

## Cross-Project Compatibility

These patterns are designed to work across jcaldwell-labs projects:

| Project | Language | Library | Notes |
|---------|----------|---------|-------|
| atari-style | Python | pygame | Primary implementation |
| boxes-live | C | SDL | Similar button mapping |

When adding joystick support to new projects, follow these conventions
for consistent user experience.

## Files

- `atari_style/core/input_handler.py` - Core input abstraction
- `atari_style/demos/joystick_test.py` - Controller testing utility
- `atari_style/demos/visualizers/shader_controller.py` - GPU shader control
- `atari_style/demos/screensaver.py` - Parametric animation control
