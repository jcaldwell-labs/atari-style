# Architecture Analysis

This document describes the current architecture of the atari-style terminal demos project, focused on understanding the rendering pipeline and identifying shader candidates.

## Overview

The atari-style project is a collection of terminal-based games, creative tools, and visual demos. The rendering is CPU-bound, using Python's blessed library for terminal output. This analysis informs the future GLSL shader integration effort.

## Core Components

### 1. Terminal Renderer (`core/renderer.py`)

The `Renderer` class implements a double-buffered terminal rendering engine.

**Key characteristics:**
- **Double buffering**: Two buffers (`buffer` for characters, `color_buffer` for colors) prevent flickering
- **Resolution**: Dynamic, based on terminal size (`term.width` x `term.height`)
- **Typical resolution**: 80-200 columns x 24-60 rows (depends on terminal)
- **FPS target**: 30-60 FPS depending on demo complexity
- **Color support**: 14 named colors via blessed terminal attributes

**Rendering flow:**
```
1. clear_buffer()     → Initialize empty buffers
2. set_pixel(x,y,c)   → Write to buffer (character + color)
3. render()           → Flush buffer to terminal via blessed
```

**Performance bottleneck**: The `render()` method iterates over every cell, even unchanged ones. For a 160x40 terminal, that's 6,400 cells per frame.

**Screenshot capability**: Can export to PNG via Pillow (used for thumbnails).

### 2. Input Handler (`core/input_handler.py`)

The `InputHandler` class provides unified keyboard and joystick input.

**Key characteristics:**
- **Keyboard**: Uses blessed's `term.inkey()` with timeout
- **Joystick**: Uses pygame for USB gamepad support
- **Axis mapping**: Analog stick → digital directions with configurable deadzone (0.15)
- **Button debouncing**: Tracks `previous_buttons` state for edge detection
- **Reconnection**: Auto-reconnects disconnected joysticks (useful for WSL USB passthrough)
- **Signal handling**: Proper cleanup on SIGINT/SIGTERM to prevent USB device lockup

**Input types:** UP, DOWN, LEFT, RIGHT, SELECT, BACK, QUIT

### 3. Menu System (`core/menu.py`)

Simple menu with `MenuItem` entries. Not relevant for shader work.

## Demo Modules

### Shader Candidates (Per-Pixel Math)

These animations compute values per-pixel per-frame — ideal for GPU parallelization.

#### 1. Plasma Animation (`screensaver.py:261-333`)

**Algorithm**: Classic demoscene plasma using summed sine waves.

```python
value = sin(x * freq_x + t)
value += sin(y * freq_y + t * 1.2)
value += sin((x + y) * freq_diag + t * 0.8)
value += sin(sqrt(x*x + y*y) * freq_radial + t * 1.5)
value = value / 4.0
```

**Parameters (4)**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| freq_x | 0.01-0.3 | Horizontal wave frequency |
| freq_y | 0.01-0.3 | Vertical wave frequency |
| freq_diag | 0.01-0.3 | Diagonal wave frequency |
| freq_radial | 0.01-0.3 | Radial wave frequency |

**GLSL suitability**: HIGH — Direct translation of trigonometric functions.

#### 2. Mandelbrot Zoomer (`screensaver.py:358-461`)

**Algorithm**: Classic Mandelbrot set iteration with escape-time coloring.

```python
z_real, z_imag = 0.0, 0.0
for i in range(max_iterations):
    if z_real*z_real + z_imag*z_imag > 4.0:
        return i
    z_real, z_imag = z_real*z_real - z_imag*z_imag + c_real, 2*z_real*z_imag + c_imag
```

**Parameters (4)**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| zoom | 0.1-1000x | Magnification level |
| center_x | -2 to 1 | X coordinate in complex plane |
| center_y | -1.5 to 1.5 | Y coordinate in complex plane |
| max_iterations | 10-200 | Escape-time iteration limit |

**Special feature**: Zoom mode toggle (button 2) for intuitive pan/zoom control.

**GLSL suitability**: HIGH — GPU excels at iterative per-pixel computation.

#### 3. Tunnel Vision (`screensaver.py:718-786`)

**Algorithm**: Raymarched tunnel with polar-to-cartesian mapping.

```python
dist = sqrt(dx*dx + dy*dy) + 0.1
angle = atan2(dy, dx)
depth = (1.0 / dist) * size * 100 + t * depth_speed
rotated_angle = angle + t * rotation_speed + depth * 0.1
```

**Parameters (4)**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| depth_speed | 0.1-5.0 | Forward motion speed |
| rotation_speed | -2 to 2 | Tunnel spin rate |
| tunnel_size | 0.3-3.0 | Tunnel diameter |
| color_cycle_speed | 0.1-3.0 | Rainbow cycle rate |

**GLSL suitability**: HIGH — Classic shader demo effect.

#### 4. Fluid Lattice (`screensaver.py:464-607`)

**Algorithm**: Wave equation simulation with rain drop perturbations.

```python
# Laplacian (discrete approximation)
laplacian = current[y-1][x] + current[y+1][x] + current[y][x-1] + current[y][x+1] - 4*current[y][x]

# Wave equation: d²u/dt² = c² ∇²u
new_value = 2*current[y][x] - previous[y][x] + wave_speed² * laplacian
new_value *= damping
```

**Parameters (4)**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| rain_rate | 0-1.5 | Drop spawn frequency |
| wave_speed | 0.05-1.0 | Wave propagation speed |
| drop_strength | 3-20 | Impact amplitude |
| damping | 0.85-0.995 | Energy decay factor |

**GLSL suitability**: MEDIUM-HIGH — Requires ping-pong buffer technique (two textures).

### Parametric Candidates (Curve Rendering)

These draw parametric curves, not per-pixel fields. Could use compute shaders or stay CPU.

#### 5. Lissajous Curve (`screensaver.py:58-147`)

**Algorithm**: Parametric curve x = sin(at), y = sin(bt + δ)

**Parameters (4)**: freqA, freqB, phase, point_count

**GLSL suitability**: MEDIUM — Could render as geometry shader or instanced points.

#### 6. Spiral Animation (`screensaver.py:150-205`)

**Algorithm**: Polar spiral r = f(θ, t)

**Parameters (4)**: num_spirals, rotation_speed, tightness, radius_scale

**GLSL suitability**: MEDIUM — Similar to Lissajous.

#### 7. Circle Wave (`screensaver.py:208-258`)

**Algorithm**: Concentric circles with radial wave modulation

**Parameters (4)**: num_circles, wave_amplitude, wave_frequency, spacing

**GLSL suitability**: LOW — Better as CPU curve rendering.

### N-Body Simulation

#### 8. Particle Swarm (`screensaver.py:610-715`)

**Algorithm**: Boid-like flocking with cohesion and separation forces.

**Parameters (4)**: num_particles (10-100), speed, cohesion, separation

**GLSL suitability**: MEDIUM — Could use compute shader, but N=100 is trivial for CPU.

### Composite Animations

Composites use one animation to modulate another's parameters.

| Composite | Source | Target | Modulation |
|-----------|--------|--------|------------|
| PlasmaLissajous | Plasma | Lissajous | Plasma value → curve frequencies |
| FluxSpiral | FluidLattice | Spiral | Wave energy → rotation speed |
| LissajousPlasma | Lissajous | Plasma | Curve phase → plasma frequencies |

**Key abstraction**: `CompositeAnimation` base class with `map_value()` for parameter remapping.

**GLSL consideration**: Could render source to texture, sample for modulation values.

## Save/Load System

**4 save slots** (buttons 2-5):
- **Hold** button: Save current animation + parameters
- **Tap** button: Load from slot

Stored data:
```python
{
    'animation_index': int,
    'parameters': dict  # Animation-specific parameter names/values
}
```

This should be preserved in the shader implementation.

## Preset System (`screensaver_presets.py`)

Pre-configured parameter sets for each animation mode (5-6 presets each):

| Animation | Example Presets |
|-----------|----------------|
| Lissajous | classic, butterfly, infinity, flower, complex |
| Plasma | classic, horizontal, vertical, radial_burst, diagonal |
| Mandelbrot | overview, seahorse_valley, spiral, deep_zoom |
| Fluid | light_rain, heavy_storm, gentle_drops, persistent_waves |
| Tunnel | classic, fast_spin, hyperspace, psychedelic |

## Performance Characteristics

### Current Limitations

| Demo | Resolution | FPS | CPU Usage |
|------|------------|-----|-----------|
| Plasma | Skip every 2nd pixel | ~30 | High |
| Mandelbrot | Skip every 2nd pixel | ~20 | Very High |
| Tunnel | Skip every 2nd pixel | ~30 | High |
| Fluid | Half-width grid | ~30 | Medium |
| Particle | 100 particles max | ~60 | Low |

### Bottlenecks

1. **Mandelbrot**: O(width × height × max_iterations) per frame
2. **Plasma/Tunnel**: O(width × height) trig operations per frame
3. **Fluid**: O(width × height) but uses half resolution
4. **Renderer**: Naïve full-screen refresh every frame

## Value Modulation System

The "value modulation" pattern allows animations to be chained:

```python
class ParametricAnimation:
    def get_value_at(self, x: int, y: int, t: float) -> float:
        """Sample animation field at point"""

    def get_global_value(self, t: float) -> float:
        """Get scalar value for entire animation"""
```

This enables composites where one animation's output drives another's input.

**Shader implication**: Render source animation to FBO, sample in target shader.

## Questions for Shader Design

1. **Framebuffer output format**: RGBA8 or RGBA16F for HDR?
2. **Terminal mapping**: How to downsample GPU output to terminal resolution?
3. **Character selection**: Use fragment shader to pick ASCII character based on brightness?
4. **Color quantization**: Reduce to 14 terminal colors in shader or post-process?
5. **Composite pipeline**: Multi-pass rendering with intermediate FBOs?

## Summary Table

| Animation | Type | Shader Priority | Complexity |
|-----------|------|-----------------|------------|
| Mandelbrot | Per-pixel | HIGH | Simple GLSL |
| Plasma | Per-pixel | HIGH | Simple GLSL |
| Tunnel | Per-pixel | HIGH | Medium GLSL |
| Fluid | Simulation | MEDIUM | Ping-pong buffers |
| Lissajous | Parametric | LOW | Geometry/Instanced |
| Spiral | Parametric | LOW | Geometry/Instanced |
| Circle Wave | Parametric | LOW | Keep CPU |
| Particle | N-body | LOW | Compute shader or CPU |
