# Screen Saver Enhancements

## Overview
Enhanced the screen saver demo with real-time joystick-controlled parametric animation controls.

## Changes Made

### 1. Parametric Controls Added to All Animations

Each of the four animations now has 4 independently adjustable parameters:

#### Lissajous Curve
- **Param 1**: Frequency X (1.0 - 10.0)
- **Param 2**: Frequency Y (1.0 - 10.0)
- **Param 3**: Phase offset (0 - 2π, wraps around)
- **Param 4**: Resolution/Points (100 - 1000)

#### Spiral Animation
- **Param 1**: Number of spirals (1 - 8)
- **Param 2**: Rotation speed multiplier (0.1 - 5.0x)
- **Param 3**: Tightness/rotations (2.0 - 15.0)
- **Param 4**: Radius scale (0.2 - 0.8)

#### Wave Circles
- **Param 1**: Number of circles (5 - 30)
- **Param 2**: Wave amplitude (0.5 - 8.0)
- **Param 3**: Wave frequency (0.1 - 2.0)
- **Param 4**: Circle spacing (1.0 - 6.0)

#### Plasma Effect
- **Param 1**: X frequency (0.01 - 0.3)
- **Param 2**: Y frequency (0.01 - 0.3)
- **Param 3**: Diagonal frequency (0.01 - 0.3)
- **Param 4**: Radial frequency (0.01 - 0.3)

### 2. 8-Directional Joystick Control

Joystick directions mapped to parameter adjustments using **opposite pairs**:

```
        UP-LEFT          UP          UP-RIGHT
        (Param 4+)    (Param 1+)    (Param 3+)
              ↖           ↑           ↗
               \          |          /
                \         |         /
    LEFT ←-------+--------•--------+------→ RIGHT
    (Param 2-)   |                 |    (Param 2+)
                /         |         \
               /          |          \
              ↙           ↓           ↘
        DOWN-LEFT        DOWN        DOWN-RIGHT
        (Param 3-)    (Param 1-)    (Param 4-)
```

**Opposite Direction Pairs**:
- UP ↔ DOWN → Parameter 1 (+/-)
- RIGHT ↔ LEFT → Parameter 2 (+/-)
- UP-RIGHT ↔ DOWN-LEFT → Parameter 3 (+/-)
- UP-LEFT ↔ DOWN-RIGHT → Parameter 4 (+/-)

**Control threshold**: 0.3 (requires moderate joystick deflection to prevent drift)

**Mode Switching**: Button 0 (not directional input)

### 3. Performance Improvements

- **Frame rate**: Increased from 30 FPS → 60 FPS
  - Changed `time.sleep(0.033)` to `time.sleep(0.016)`
- **Animation speed**: 2x multiplier applied to `dt` in update loop
- **Smoother animations**: Higher frame rate provides more fluid parameter transitions

### 4. Real-Time Parameter Display

- Parameter values displayed on-screen in bright green
- Shows current values for all 4 parameters of active animation
- Updates live as joystick adjusts values
- Located in top-left below mode indicator

### 5. Updated UI/Controls

New control indicators:
- "Joystick Dirs: Adjust Params"
- Parameter value display with descriptive names
- Updated help text on right side

## Implementation Details

### Base Class Enhancement
Added to `ParametricAnimation` base:
- `adjust_params(param: int, delta: float)` - Adjust parameter by delta
- `get_param_info() -> list` - Return formatted parameter strings for display

### Input Handling
- Joystick state checked every frame
- 8-direction detection with diagonal support
- 50ms delay after parameter adjustment prevents rapid-fire changes
- Independent of button-based input system

### Code Structure
```python
# Each animation class now has:
def __init__(self):
    self.param1 = default_value
    self.param2 = default_value
    # ... etc

def adjust_params(self, param: int, delta: float):
    # Clamp values to valid ranges
    if param == 1:
        self.param1 = max(min_val, min(max_val, self.param1 + delta))

def get_param_info(self) -> list:
    return [
        f"Param Name: {self.param1:.1f}",
        # ... etc
    ]
```

## Usage

1. Launch screen saver from menu
2. Use joystick directions to adjust parameters:
   - Push up/down for parameter 1
   - Push left/right for parameter 2
   - Push diagonally up-right/down-right for parameter 3
   - Push diagonally up-left/down-left for parameter 4
3. Watch parameter values update in real-time (top-left)
4. Switch animation modes to explore different parameter sets

## Testing

To test parametric controls:
```bash
source venv/bin/activate
python run.py
# Select "Screen Saver"
# Use joystick to adjust parameters in all 8 directions
# Observe parameter value changes and visual effects
```

## Benefits

1. **Interactive exploration** - Users can discover interesting parameter combinations
2. **Educational** - Visualize how mathematical parameters affect animations
3. **Creative** - Generate unique visual patterns on the fly
4. **Full joystick utilization** - Makes use of all 8 directions plus buttons

## Documentation Updates

- `CONTROLS.md` - Added detailed parameter mapping and ranges
- `README.md` - Updated screen saver description with new features
- `CLAUDE.md` - Enhanced architecture documentation with parametric controls
- Added joystick utility references (qjoypad, antimicrox)
