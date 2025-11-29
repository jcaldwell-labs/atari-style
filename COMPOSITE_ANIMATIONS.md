# Composite Screen Saver Animations

## Overview

Composite animations are a new feature that combines two parametric animations in interesting ways. One animation acts as a **modulation source**, providing values that drive the parameters of another animation (the **target**). This creates emergent visual behaviors that are more dynamic and interesting than either animation alone.

## How It Works

### Modulation System

Every parametric animation now implements two methods:

1. **`get_value_at(x, y, t)`** - Returns a normalized value (-1.0 to 1.0) at a specific screen position
2. **`get_global_value(t)`** - Returns a single normalized value representing the overall animation state

These values are used to **drive** or **modulate** the parameters of other animations in real-time.

### Value Mapping

The `CompositeAnimation` base class provides value mapping functions:

- **Linear**: Direct proportional mapping
- **Quadratic**: Eased transitions with quadratic curve
- **Sine**: Smooth sinusoidal easing

Values from the source animation (in range [-1, 1]) are mapped to the target parameter's valid range.

## Available Composite Animations

### 1. Plasma → Lissajous

**Description**: The plasma field's undulating waves drive the Lissajous curve's X and Y frequencies, causing the curve to continuously morph and evolve.

**How it works**:
- Plasma samples its center point value
- This value modulates `freq_x` (range 2.0 to 6.0)
- Inverse value modulates `freq_y` (creates contrast)
- Result: Curve shape morphs as plasma waves oscillate

**Visual effect**: The Lissajous curve appears to "breathe" and transform, following the rhythm of the plasma field.

**Controls**:
- **Param 1 (↑/↓)**: Modulation strength (how much plasma affects the curve)
- **Params 2-4**: Target Lissajous parameters

**Best settings**:
- Modulation strength: 0.8-1.2x
- Watch as curve complexity increases/decreases with plasma waves

---

### 2. Flux → Spiral

**Description**: The fluid lattice wave energy drives the spiral's rotation speed, causing it to pulse and spin with the rhythm of the waves.

**How it works**:
- Fluid lattice calculates average wave height across the field
- This energy level modulates rotation speed (range 0.5 to 3.0)
- Additional modulation of tightness creates extra visual interest
- Result: Spiral appears to "respond" to wave impacts

**Visual effect**: The spiral spins faster when waves are active, slower during calm periods. Creates a sense of the spiral being "pushed" by invisible waves.

**Controls**:
- **Param 1 (↑/↓)**: Modulation strength
- **Params 2-4**: Target spiral parameters

**Best settings**:
- Modulation strength: 1.0-1.5x
- Higher rain rate in fluid source creates more dramatic pulses

---

### 3. Lissajous → Plasma

**Description**: The Lissajous curve's smooth oscillation drives the plasma field's frequency parameters, creating synchronized wave patterns.

**How it works**:
- Lissajous phase angle (sine wave) provides modulation value
- This drives plasma X and Y frequencies
- Creates harmonic relationship between curve and field
- Result: Plasma colors shift in sync with curve motion

**Visual effect**: The plasma field appears to "dance" with the Lissajous curve, with color waves synchronized to the curve's rhythm.

**Controls**:
- **Param 1 (↑/↓)**: Modulation strength
- **Params 2-4**: Target plasma parameters

**Best settings**:
- Modulation strength: 0.5-1.0x
- Lower frequencies create more visible synchronization

---

## Technical Details

### Architecture

```
ParametricAnimation (base class)
    ├── get_value_at(x, y, t) → float
    └── get_global_value(t) → float

CompositeAnimation (extends ParametricAnimation)
    ├── source: ParametricAnimation
    ├── target: ParametricAnimation
    ├── modulation_strength: float
    ├── modulation_mapping: str
    └── map_value(value, min, max) → float
```

### Modulation Interface Implementation

**PlasmaAnimation**:
- `get_value_at`: Returns plasma value at pixel (4-wave sine sum)
- `get_global_value`: Samples 9 points near center, returns average

**LissajousCurve**:
- `get_value_at`: Returns normalized distance to nearest curve point
- `get_global_value`: Returns sin(t) for smooth oscillation

**FluidLattice**:
- `get_value_at`: Returns normalized wave height at lattice cell
- `get_global_value`: Samples every 4th cell, returns average energy

### Performance

Composite animations run at 30-60 FPS depending on complexity:
- **Plasma → Lissajous**: ~50-60 FPS (Lissajous is lightweight)
- **Flux → Spiral**: ~40-50 FPS (fluid simulation is heavier)
- **Lissajous → Plasma**: ~30-40 FPS (plasma rendering is expensive)

## Creating Custom Composites

You can create your own composite animations by extending `CompositeAnimation`:

```python
class MyComposite(CompositeAnimation):
    def __init__(self, renderer):
        source = SourceAnimation(renderer)
        target = TargetAnimation(renderer)
        super().__init__(renderer, source, target)
        
        # Configure source and target
        self.source.some_param = value
        
    def draw(self, t: float):
        # Get modulation value
        mod_value = self.source.get_global_value(t)
        
        # Modulate target parameter(s)
        self.target.param1 = self.map_value(mod_value, min_val, max_val)
        
        # Draw modulated target
        self.target.draw(t)
```

## Future Composite Possibilities

See `COMPOSITE_ANIMATION_ANALYSIS.md` and `GITHUB_ISSUES.md` for detailed plans:

### Spatial Blending (Phase 2)
- **Plasma Textured Tunnel**: Plasma provides texture for tunnel walls
- **Particle Fluid Interaction**: Particles create ripples, waves push particles

### Temporal Synchronization (Phase 3)
- **Dual Lissajous**: Two curves with harmonic ratios create interference
- **Triple Plasma RGB**: Phase-shifted plasma for each color channel

### Feedback Systems (Advanced)
- **Bidirectional coupling**: Animations influence each other mutually
- **Emergent behaviors**: Complex patterns from simple rules

## Using Composites

### In the Screen Saver Menu

1. Launch the screen saver
2. Press **→** to cycle through animations
3. Animations 9-11 are composites (look for **→** in the name)
4. Press **H** to see help for the current composite

### From Python

```python
from atari_style.demos.screensaver import PlasmaLissajous
from atari_style.core.renderer import Renderer

renderer = Renderer()
composite = PlasmaLissajous(renderer)

# Adjust modulation
composite.modulation_strength = 1.5
composite.modulation_mapping = "sine"

# Run
try:
    renderer.enter_fullscreen()
    while True:
        composite.draw(time.time())
        composite.update(0.033)
        renderer.render()
        time.sleep(0.033)
finally:
    renderer.exit_fullscreen()
```

### In Demo Mode

```python
from atari_style.demos.screensaver_demo import ScreenSaverDemo

# Composites are automatically included in the demo
demo = ScreenSaverDemo()
demo.run_demo(duration=200)
```

## Mathematical Background

### Value Normalization

All modulation values are normalized to [-1, 1]:
- **Plasma**: 4-wave sum divided by 4
- **Lissajous**: Phase angle via sin(t)
- **Fluid**: Wave height clamped and scaled

This ensures consistent behavior across different source animations.

### Harmonic Relationships

When frequencies are modulated, harmonic ratios emerge:
- **2:3 ratio**: Classic musical fifth
- **3:4 ratio**: Perfect fourth
- **Phase offsets**: Create beating patterns

### Emergent Behavior

Composites exhibit behaviors neither source nor target shows alone:
- **Resonance**: When modulation matches natural frequency
- **Chaos**: Small changes in source create large changes in target
- **Stability**: Some parameter ranges create stable patterns

## Troubleshooting

### Composite looks static
- Increase modulation strength (Param 1 ↑)
- Check source animation has variation (some configs are stable)
- Try different modulation mapping (cycle with M key - if implemented)

### Too much chaos
- Decrease modulation strength (Param 1 ↓)
- Reduce source animation parameter ranges
- Use quadratic or sine mapping for smoother transitions

### Performance issues
- Composites using plasma as target are slower
- Reduce update frequency or screen resolution if needed
- Close other applications

## See Also

- **COMPOSITE_ANIMATION_ANALYSIS.md** - Detailed analysis of all possibilities
- **GITHUB_ISSUES.md** - Implementation roadmap and detailed specs
- **ANIMATIONS-VISUAL-GUIDE.md** - Visual guide to all animations
- **test_composite_animations.py** - Unit tests demonstrating usage
