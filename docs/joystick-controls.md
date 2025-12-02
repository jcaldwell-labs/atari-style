# Joystick Controls

This document describes joystick control patterns used in atari-style and compatible projects.

## Supported Controllers

Any USB/Bluetooth controller compatible with pygame/SDL should work:

| Controller | Notes |
|------------|-------|
| Xbox (360/One/Series) | Full support, recommended |
| PlayStation (DS4/DualSense) | Full support |
| 8BitDo controllers | Full support |
| Generic USB gamepads | Varies by model |

## Standard Control Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                      CONTROLLER LAYOUT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────┐         ┌─────┐                      │
│                    │ LB  │         │ RB  │                      │
│                    └─────┘         └─────┘                      │
│                    ┌─────┐         ┌─────┐                      │
│                    │ LT  │         │ RT  │                      │
│                    └─────┘         └─────┘                      │
│                                                                  │
│         ┌───┐                               ┌───┐               │
│         │ ▲ │                               │ Y │               │
│     ┌───┼───┼───┐                       ┌───┼───┼───┐           │
│     │ ◄ │   │ ► │  D-Pad                │ X │   │ B │  Face     │
│     └───┼───┼───┘                       └───┼───┼───┘  Buttons  │
│         │ ▼ │                               │ A │               │
│         └───┘                               └───┘               │
│                                                                  │
│           ╭───╮                         ╭───╮                   │
│          ╱     ╲                       ╱     ╲                  │
│         │   ●   │  Left Stick         │   ●   │  Right Stick   │
│          ╲     ╱                       ╲     ╱                  │
│           ╰───╯                         ╰───╯                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Button Assignments

### Core Controls (All Demos)

| Button | Xbox | PlayStation | Function |
|--------|------|-------------|----------|
| Button 0 | A | Cross (X) | Select / Confirm / Fire |
| Button 1 | B | Circle (O) | Back / Cancel |
| Left Stick | Left Stick | Left Stick | Navigation / Movement |

### Extended Controls (Where Applicable)

| Button | Xbox | PlayStation | Function |
|--------|------|-------------|----------|
| Button 2 | X | Square | Secondary action |
| Button 3 | Y | Triangle | Toggle mode / Help |
| D-Pad | D-Pad | D-Pad | Alternative navigation |
| LB/RB | LB/RB | L1/R1 | Cycle options |
| LT/RT | LT/RT | L2/R2 | Speed / Intensity control |

## Application-Specific Mappings

### Menu Navigation

```
Left Stick / D-Pad    Navigate menu items
Button 0 (A)          Select item
Button 1 (B)          Back / Exit
```

### Games (Pac-Man, Galaga, etc.)

```
Left Stick            Movement (4 or 8 directions)
Button 0 (A)          Fire / Action
Button 1 (B)          Pause / Menu
```

### Screen Saver / Visualizers

```
Left Stick X          Parameter 1 control
Left Stick Y          Parameter 2 control
Right Stick X         Parameter 3 control (if supported)
Right Stick Y         Parameter 4 control (if supported)
Button 0 (A)          Cycle animation mode
Button 1 (B)          Exit to menu
Button 2 (X)          Reset parameters
Button 3 (Y)          Toggle help overlay
D-Pad Up/Down         Speed adjustment
D-Pad Left/Right      Color mode cycle
```

### ASCII Painter

```
Left Stick            Move cursor
Button 0 (A)          Draw / Place character
Button 1 (B)          Erase / Undo
Button 2 (X)          Cycle tool
Button 3 (Y)          Cycle color
D-Pad                 Fine cursor movement
```

## Technical Details

### Deadzone

A 15% deadzone is applied to analog sticks to prevent drift:

```python
deadzone = 0.15
x = x if abs(x) > deadzone else 0.0
y = y if abs(y) > deadzone else 0.0
```

### Axis Ranges

- Raw axis values: `-1.0` to `+1.0`
- After deadzone: `0.0` or `-1.0` to `+1.0`
- Digital threshold: `0.5` (for menu navigation)

### Button States

Buttons use edge detection to prevent repeated triggers:

```python
# Only fires on initial press, not while held
if is_pressed and not was_pressed:
    handle_button_press()
```

## Keyboard Fallback

When no joystick is detected, keyboard controls are available:

| Key | Function |
|-----|----------|
| Arrow Keys / WASD | Navigation / Movement |
| Enter / Space | Select / Confirm |
| Escape / Q | Back / Exit |
| X | Quit application |

## Troubleshooting

### Joystick Not Detected

1. **Check connection**: Ensure controller is plugged in before starting
2. **USB passthrough (WSL)**: Use `usbipd` to attach controller
3. **Permissions (Linux)**: Add user to `input` group
4. **Driver issues**: Try reconnecting or rebooting

### Joystick Test Utility

Run the built-in joystick test to verify your controller:

```bash
python -c "from atari_style.demos.tools.joystick_test import run_joystick_test; run_joystick_test()"
```

This displays:
- Controller name and connection status
- Real-time axis positions (visual crosshair)
- Button press indicators
- Raw axis values

### Automatic Reconnection

If the joystick disconnects during use (common with USB passthrough), the system will:
1. Detect the disconnection within 1 second
2. Attempt reconnection every ~30 frames
3. Display "Joystick reconnected" when successful
4. Restore button state tracking automatically

### WSL2 USB Passthrough

To use a USB joystick in WSL2:

```powershell
# In Windows PowerShell (Admin)
usbipd list                          # Find your controller
usbipd bind --busid <BUSID>          # Bind (one-time)
usbipd attach --wsl --busid <BUSID>  # Attach to WSL
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Stick drifts | Increase deadzone or recalibrate controller |
| Buttons stuck | Release all buttons and reconnect |
| Wrong mapping | Check controller mode (XInput vs DirectInput) |
| Lag/delay | Close other controller-using applications |

## Cross-Project Compatibility

This control scheme is shared with [boxes-live](https://github.com/jcaldwell-labs/boxes-live) for consistent user experience across projects:

| Control | atari-style | boxes-live |
|---------|-------------|------------|
| Left Stick | Movement / Parameters | Pan canvas / Move selection |
| Button 0 | Select / Fire | Select box / Confirm |
| Button 1 | Back / Cancel | Deselect / Exit focus |

## Related

- `atari_style/core/input_handler.py` - Input handling implementation
- `atari_style/demos/tools/joystick_test.py` - Joystick verification utility
- [boxes-live](https://github.com/jcaldwell-labs/boxes-live) - Terminal canvas with joystick support
