# Screen Saver Animations - Visual Guide

## 🎨 All 8 Animations Explained

---

## 1️⃣ Lissajous Curve
```
    ╭─────╮
   ╱       ╲
  ●         ●     Mathematical curve formed by
 ╱           ╲    plotting sin(ax+δ) vs sin(by)
●             ●
 ╲           ╱    Creates figure-8, loops, roses
  ●         ●
   ╲       ╱
    ╰─────╯
```
**Type**: Mathematical
**Visual**: Smooth curves in rainbow colors
**Parameters**: Frequency ratios, phase shift, resolution

---

## 2️⃣ Spiral
```
        ●
      ○   ●        Multiple spirals rotating
    ·       ○      and expanding outward
  ●           ·
    ·       ○      Arms interweave in patterns
      ○   ●
        ●
```
**Type**: Geometric
**Visual**: Cyan gradient spirals
**Parameters**: Number of arms, speed, tightness, size

---

## 3️⃣ Wave Circles
```
    ○ ○ ○ ○ ○
   ○         ○     Concentric circles that
  ○           ○    pulse with sine wave
 ○             ○
  ○           ○    Creates ripple effects
   ○         ○
    ○ ○ ○ ○ ○
```
**Type**: Geometric
**Visual**: Rainbow colored concentric rings
**Parameters**: Count, wave amplitude, frequency, spacing

---

## 4️⃣ Plasma
```
░▒▓█▓▒░
▒▓█ █▓▒         Multi-frequency sine wave
▓█   █▓         interference pattern
█     █
▓█   █▓         Creates organic flowing shapes
▒▓█ █▓▒
░▒▓█▓▒░
```
**Type**: Mathematical
**Visual**: Colored blocks with varying density
**Parameters**: 4 different frequency components

---

## 5️⃣ Mandelbrot Zoomer ⭐ NEW
```
    ,,,,                Infinite zoom into the
  ·······               famous Mandelbrot fractal
 ·○●○●○·
 ·●███●·                Red = quick escape
 ·○●○●○·                Blue = in the set
  ·······               Cyan = boundary regions
    ,,,,
```
**Type**: Fractal
**Visual**: Color-coded by iteration count
**Parameters**: Zoom (0.1-1000x), center X/Y, detail

**Math**: z(n+1) = z(n)² + c

---

## 6️⃣ Fluid Lattice ⭐ NEW
```
        ●                Random rain drops
      ○ ● ○              create ripples
    ·   ●   ·
  ·     ●     ·          Waves propagate and
    ·   ●   ·            interfere across grid
      ○ ● ○
        ●                Real wave physics!
```
**Type**: Physics Simulation
**Visual**: Blue/cyan waves with intensity
**Parameters**: Wave speed, damping, rain rate, drop power

**Physics**: d²u/dt² = c²∇²u (wave equation)

---

## 7️⃣ Particle Swarm ⭐ NEW
```
  ● ·
     ● ·      ●          10-100 particles with
  ● ·    ● ·             flocking behavior
     ●      ● ·
  ● ·    ● ·             Cohesion + separation
     ●   ● ·    ●        creates emergent patterns
  ● ·      ● ·
     ●    ● ·            Rainbow colored!
```
**Type**: AI/Physics (Boids)
**Visual**: Colored particles with motion trails
**Parameters**: Count, speed, cohesion, separation

**Algorithm**: Simplified Reynolds' boids

---

## 8️⃣ Tunnel Vision ⭐ NEW
```
▒▓█████████▓▒
░▒▓███████▓▒░          Classic demo-scene
  ░▒▓███▓▒░            infinite tunnel
    ░▒▓▒░
  ░▒▓███▓▒░            Scrolling + rotation
░▒▓███████▓▒░          with color cycling
▒▓█████████▓▒
```
**Type**: Demo-Scene Effect
**Visual**: Checkerboard tunnel pattern
**Parameters**: Depth speed, rotation, size, color speed

**Math**: Polar coordinates with 1/r depth mapping

---

## Joystick Control Map

```
        UP-LEFT          UP          UP-RIGHT
        (Param 4+)    (Param 1+)    (Param 3+)
              ↖           ↑           ↗
               \          |          /
                \         |         /
    LEFT ←-------+--------●--------+------→ RIGHT
    (Param 2-)   |                 |    (Param 2+)
                /         |         \
               /          |          \
              ↙           ↓           ↘
        DOWN-LEFT        DOWN        DOWN-RIGHT
        (Param 3-)    (Param 1-)    (Param 4-)
```

**Opposite directions control the same parameter!**

---

## Animation Comparison

| Animation | Complexity | FPS | CPU Load | Visual Density |
|-----------|------------|-----|----------|----------------|
| Lissajous | Low | 60 | Low | Medium |
| Spiral | Low | 60 | Low | Medium |
| Wave Circles | Low | 60 | Low | High |
| Plasma | Medium | 60 | Medium | Very High |
| Mandelbrot | High | 60 | High | High |
| Fluid Lattice | Medium | 60 | Medium | Medium |
| Particle Swarm | Low | 60 | Low | Low |
| Tunnel | Low | 60 | Medium | Very High |

---

## Visual Characteristics

### Color Palettes

**Original Animations**:
- Lissajous: Rainbow gradient
- Spiral: Cyan gradient
- Wave Circles: Rainbow rings
- Plasma: Full spectrum blocks

**New Animations**:
- Mandelbrot: Red/Yellow→Green/Cyan→Blue
- Fluid: Blue/Cyan intensity scale
- Particles: Rainbow (one color per particle)
- Tunnel: Cycling rainbow

### Character Sets

**Smooth**: `·○●█` (Mandelbrot, Fluid, Particles)
**Density**: `░▒▓█` (Plasma, Tunnel)
**Geometric**: `─│┌┐└┘` (Borders, menus)

---

## Recommended Parameter Settings

### Lissajous Beautiful Patterns
- Freq X: 3, Freq Y: 4 (classic)
- Freq X: 5, Freq Y: 7 (complex)
- Phase: π/2 for symmetry

### Spiral Hypnotic Effect
- Spirals: 5-6 for density
- Speed: 0.5 for slow motion
- Tightness: 10+ for tight coils

### Mandelbrot Famous Regions
- "Seahorse Valley": X=-0.75, Y=0.1, Zoom=100
- "Elephant Valley": X=0.3, Y=0.03, Zoom=50
- Classic view: X=-0.5, Y=0, Zoom=1

### Fluid Realistic Waves
- Wave Speed: 0.5, Damping: 0.95 (realistic)
- Rain Rate: 0.3, Drop Power: 8 (active)

### Particles Tight Flocking
- Particles: 70+
- Cohesion: 1.5, Separation: 0.5

### Tunnel Psychedelic Mode
- Depth: 3.0+ (fast)
- Rotation: ±1.5 (spinning)
- Color Speed: 2.5+ (rainbow)

---

## Performance Tips

**For slower terminals**:
- Stick with Lissajous, Spiral, Particles (low complexity)
- Reduce Mandelbrot detail (use 20-30 iterations)
- Lower particle count (20-30)

**For fast terminals**:
- Max out Mandelbrot detail (150-200)
- High particle counts (80-100)
- Fast tunnel depth speeds (4-5)

---

## Educational Value

**Math Concepts**:
- Parametric equations (Lissajous)
- Polar coordinates (Spiral, Tunnel)
- Complex numbers (Mandelbrot)
- Partial differential equations (Fluid)

**Physics**:
- Wave propagation (Fluid)
- Damped oscillations (Fluid)
- Emergent behavior (Particles)
- Perspective projection (Tunnel)

**Computer Science**:
- Real-time rendering
- Numerical methods (Mandelbrot, Fluid)
- Agent-based simulation (Particles)
- Optimization techniques (all)

---

## Quick Start Guide

1. **Launch**: `python run.py` → Select "Screen Saver"
2. **Explore**: Press Button 0 to cycle through 8 modes
3. **Adjust**: Use joystick directions to tweak parameters
4. **Watch**: See parameter values update on-screen (top-left)
5. **Experiment**: Try extreme values and find sweet spots!

**Tip**: Start with Particle Swarm or Tunnel - they're the most immediately interactive!

---

## ASCII Art Examples

### Mandelbrot (zoomed in)
```
........
.○○○○○○.
.○●██●○.
.○●██●○.
.○○○○○○.
........
```

### Fluid Lattice (ripples)
```
    ·
   ○●○
  ·●█●·
   ○●○
    ·
```

### Particle Swarm (flocking)
```
   ●·
  ●· ●·
   ●·  ●·
  ●· ●·
   ●·
```

### Tunnel (looking down)
```
█▓▒░  ░▒▓█
 ▓▒░░▒▓
  ▒░░▒
   ░░
  ▒░░▒
 ▓▒░░▒▓
█▓▒░  ░▒▓█
```

---

## Have Fun Exploring! 🎮✨
