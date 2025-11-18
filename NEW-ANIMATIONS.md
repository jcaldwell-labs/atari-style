# New Screen Saver Animations

## Overview
Added 4 new parametric animations to the screen saver, doubling the total count from 4 to 8.

## New Animations

### 5. Mandelbrot Zoomer
**Description**: Interactive exploration of the Mandelbrot fractal set

**Features**:
- Real-time Mandelbrot set calculation
- Infinite zoom capability with auto-zoom animation
- Adjustable center point for exploring different regions
- Color-coded by iteration count (escape time)
- Performance optimized with 2x2 pixel sampling

**Parameters**:
- **Zoom** (0.1 - 1000x): Zoom level with multiplicative adjustment
- **Center X** (-2.0 to 1.0): Real part of complex center
- **Center Y** (-1.5 to 1.5): Imaginary part of complex center
- **Detail** (10 - 200): Maximum iterations for precision

**Visual**: Red/Yellow (fast escape) → Green/Cyan (medium) → Blue (in set)

---

### 6. Fluid Lattice
**Description**: Real-time wave simulation with rain drop perturbations

**Features**:
- 2D wave equation solver using finite differences
- Random rain drops create ripples
- Wave propagation and interference patterns
- Adjustable physics parameters

**Parameters** (Refined for better visibility):
- **Rain Rate** (0.0 - 1.5): Frequency of random drops [Default: 0.35]
  - UP/DOWN: Most visible control - more rain = more action!
- **Wave Speed** (0.05 - 1.0): Propagation velocity [Default: 0.3]
  - LEFT/RIGHT: Horizontal = speed - intuitive!
- **Drop Power** (3 - 20): Impact strength of rain drops [Default: 8.0]
  - UP-RIGHT/DOWN-LEFT: Bigger splashes!
- **Damping** (0.85 - 0.995): Energy dissipation [Default: 0.97]
  - UP-LEFT/DOWN-RIGHT: Higher = waves last longer

**Visual**: Blue/Cyan waves with intensity-based characters (·○●█)

**Physics**: Implements d²u/dt² = c²∇²u with damping

---

### 7. Particle Swarm
**Description**: Boid-like flocking behavior simulation

**Features**:
- Up to 100 particles with emergent behavior
- Cohesion (attraction to group center)
- Separation (avoidance of neighbors)
- Velocity vectors visualized as trails
- Toroidal wrap-around boundaries

**Parameters**:
- **Particles** (10 - 100): Number of active particles
- **Speed** (0.5 - 5.0): Maximum velocity
- **Cohesion** (0.0 - 2.0): Attraction strength to center of mass
- **Separation** (0.0 - 3.0): Repulsion strength from neighbors

**Visual**: Rainbow-colored particles (●) with motion trails (·)

**Algorithm**: Simplified boids with two forces (cohesion + separation)

---

### 8. Tunnel Vision
**Description**: Classic demo-scene tunnel effect

**Features**:
- Perspective tunnel with polar coordinate mapping
- Continuous depth scrolling
- Rotation animation
- Checkerboard pattern texture
- Color cycling along depth

**Parameters**:
- **Depth Speed** (0.1 - 5.0): Forward motion speed
- **Rotation** (-2.0 to 2.0): Angular velocity (can reverse)
- **Size** (0.3 - 3.0): Tunnel diameter
- **Color Speed** (0.1 - 3.0): Color animation rate

**Visual**: Rotating tunnel with alternating block patterns (█▓▒)

**Math**: Uses 1/r depth mapping and angle-based rotation

---

## Implementation Details

### Performance Optimizations

**Mandelbrot**:
- 2x2 pixel skip for reduced computation
- Early bailout at r² > 4
- Clamped iteration count

**Fluid Lattice**:
- Half-width rendering (every 2nd column)
- Sparse updates (border pixels static)
- Double buffering for wave equation

**Particle Swarm**:
- Pre-allocated particle pool
- Active/inactive particle toggle
- Distance check short-circuit

**Tunnel**:
- 2x horizontal pixel skip
- Pre-computed color palette
- Integer modulo for patterns

### Common Features

All new animations:
- ✅ 4 adjustable parameters
- ✅ `adjust_params()` method
- ✅ `get_param_info()` for HUD display
- ✅ 60 FPS compatible
- ✅ Opposite joystick pair controls
- ✅ Terminal-safe character sets

## Technical Complexity

| Animation | Complexity | Physics | Math Intensity |
|-----------|------------|---------|----------------|
| Mandelbrot | High | No | Very High |
| Fluid Lattice | Medium | Yes | High |
| Particle Swarm | Low | Yes | Medium |
| Tunnel | Low | No | Medium |

## Usage Examples

### Mandelbrot Exploration
1. Select "Mandelbrot Zoomer" mode
2. Use UP/DOWN to zoom in/out
3. Use LEFT/RIGHT to pan horizontally
4. Use diagonals to adjust center and detail
5. Find interesting regions (e.g., -0.7, 0.0 at high zoom)

### Fluid Dynamics
1. Select "Fluid Lattice" mode
2. **Increase rain rate** (UP) to see more ripples - most dramatic effect!
3. **Adjust wave speed** (LEFT/RIGHT) - slower shows waves better
4. **Increase drop power** (UP-RIGHT) for bigger splashes
5. **Increase damping** (UP-LEFT) for waves that last longer
6. Try: Max rain (UP), slow waves (LEFT), high damping (UP-LEFT) = beautiful ripples!

### Swarm Behavior
1. Select "Particle Swarm" mode
2. Increase particles (UP) to see emergent patterns
3. High cohesion (UP-RIGHT) = tight flocking
4. High separation (UP-LEFT) = dispersed motion
5. Balance both for realistic swarming

### Tunnel Immersion
1. Select "Tunnel Vision" mode
2. Increase depth speed (UP) for fast travel
3. Adjust rotation (LEFT/RIGHT) for spinning
4. Increase size (UP-RIGHT) for wider tunnel
5. Fast color speed for psychedelic effect

## Future Enhancements

Possible additions:
- Julia set explorer (similar to Mandelbrot)
- Conway's Game of Life with adjustable rules
- 3D wireframe rotation
- Perlin noise terrain
- Fire effect simulation
- Matrix digital rain

---

## Testing

All animations tested with:
```bash
source venv/bin/activate
python test_new_animations.py
python run.py  # Select "Screen Saver"
```

Expected behavior:
- ✅ All 8 animations load
- ✅ Parameters adjust smoothly
- ✅ No crashes or exceptions
- ✅ 60 FPS maintained
- ✅ Joystick controls responsive
