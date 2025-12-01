# GLSL Shader Integration Roadmap

## Overview

The screensaver animations in atari-style are currently implemented as CPU-bound per-pixel Python computations. This limits performance, especially for complex effects like Mandelbrot zoom and Plasma. By porting these effects to GLSL fragment shaders, we can achieve:

- **60+ FPS** at 1080p and higher resolutions
- **Real-time CRT post-processing** (scanlines, barrel distortion, color bleeding)
- **More complex parameter exploration** without performance penalties
- **Richer visual effects** that would be impractical on CPU

This document outlines the phased approach to adding GPU-accelerated rendering.

## Current State

The project uses a CPU-based terminal renderer (`core/renderer.py`) with double buffering via the blessed library. All visual effects compute per-pixel values in Python, which becomes a bottleneck for full-screen effects.

### Shader Candidates (from screensaver.py)

| Animation | Type | Parameters | Priority | Notes |
|-----------|------|------------|----------|-------|
| Mandelbrot | Fractal zoom | centerX, centerY, zoom, maxIter | High | O(w×h×iterations), severe CPU bottleneck |
| Plasma | Demoscene classic | freq_x, freq_y, freq_diag, freq_radial | High | 4 trig ops per pixel |
| Tunnel Vision | Raymarching | depth_speed, rotation, size, color_speed | High | Classic shader demo effect |
| Fluid Lattice | Wave simulation | rain_rate, wave_speed, drop_strength, damping | Medium | Requires ping-pong buffers |
| Lissajous | Parametric curve | freqA, freqB, phase, points | Low | Could use geometry shader or stay CPU |
| Spiral | Parametric | num_spirals, rotation, tightness, scale | Low | Similar to Lissajous |
| Wave Circle | Concentric rings | circles, amplitude, frequency, spacing | Low | Simple, keep CPU |
| Particle Swarm | N-body | count, speed, cohesion, separation | Medium | Compute shader candidate (N≤100) |

### Non-Candidates (keep as-is)

- **Games** (Pacman, Galaga, Grand Prix, Breakout) — Game logic, not visual effects
- **ASCII Painter** — Interactive tool, not visualization
- **Joystick Test** — Utility diagnostic
- **Platonic Solids** — 3D wireframe, CPU adequate for low poly count
- **Starfield** — Particle-based, CPU adequate for current star count

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Python: main.py, menu system, input handling)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     GLRenderer (core/gl/)                    │
│  - moderngl context management                               │
│  - Shadertoy-compatible uniforms (iTime, iResolution, etc.) │
│  - Fullscreen quad rendering                                 │
│  - Framebuffer management                                    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Effect Shader  │ │  Effect Shader  │ │  Effect Shader  │
│  (Mandelbrot)   │ │    (Plasma)     │ │    (Tunnel)     │
│                 │ │                 │ │                 │
│ shaders/effects │ │ shaders/effects │ │ shaders/effects │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Post-Process Chain                        │
│  - CRT scanlines                                             │
│  - Barrel distortion                                         │
│  - Color palette reduction (Atari 128-color)                 │
│  shaders/post/                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Output Options                          │
│  - Direct GPU window (via pygame/GLFW)                       │
│  - Terminal downsampling (GPU → ASCII characters)            │
│  - Video export (MP4/GIF)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (PR #2)

**Goal**: Establish OpenGL rendering infrastructure.

- [ ] Add `moderngl>=5.8.0` dependency to requirements.txt
- [ ] Create `GLRenderer` base class in `core/gl/renderer.py`
  - OpenGL context via moderngl (headless or pygame window)
  - Fullscreen quad VAO/VBO setup
  - Uniform management (time, resolution, mouse/joystick)
- [ ] Implement Shadertoy-compatible uniform system:
  ```glsl
  uniform float iTime;
  uniform vec2 iResolution;
  uniform vec4 iMouse;  // or iJoystick for our use case
  uniform vec4 iParams; // 4 adjustable parameters
  ```
- [ ] Basic shader loading and hot-reload support
- [ ] Simple test shader (solid color gradient)

**Deliverables**: Ability to render a GLSL shader to a window.

### Phase 2: First Effect (PR #3)

**Goal**: Port one complete effect to GLSL.

- [ ] Create `shaders/effects/mandelbrot.frag`
  - Escape-time coloring
  - Smooth iteration interpolation
  - Parameter uniforms for zoom/pan/iterations
- [ ] Implement joystick → uniform mapping
  - Same 4-parameter diagonal control scheme as CPU version
- [ ] Side-by-side comparison mode (CPU vs GPU)
- [ ] Performance benchmarks (FPS, GPU utilization)

**Deliverables**: Mandelbrot running on GPU with joystick control.

### Phase 3: Post-Processing (PR #4)

**Goal**: Add CRT-style visual effects.

- [ ] Create `shaders/post/crt.frag`
  - Scanline overlay (configurable intensity)
  - RGB shadow mask pattern
  - Barrel distortion (curvature parameter)
  - Vignette darkening at edges
- [ ] Create `shaders/post/palette.frag`
  - Reduce to Atari 128-color palette
  - Optional dithering (Bayer, ordered)
- [ ] Multi-pass rendering pipeline
- [ ] Toggle effects on/off at runtime

**Deliverables**: Authentic retro CRT look.

### Phase 4: Effect Library (PR #5+)

**Goal**: Port remaining effects one by one.

- [ ] Plasma (`shaders/effects/plasma.frag`)
- [ ] Tunnel Vision (`shaders/effects/tunnel.frag`)
- [ ] Fluid Lattice (`shaders/effects/fluid.frag`) — ping-pong technique
- [ ] Parametric curves (Lissajous, Spiral) — evaluate approach

**Per-effect checklist**:
1. Create GLSL fragment shader
2. Map existing Python parameters to uniforms
3. Verify visual parity with CPU version
4. Add to effect selector menu
5. Document in shader source

### Phase 5: Composites & Advanced (PR #6+)

**Goal**: Recreate composite animations in shader pipeline.

- [ ] Multi-texture compositing (source → target modulation)
- [ ] Shader chaining (effect → effect → post)
- [ ] Save slot system for GPU renderer
- [ ] Preset tour mode

## Uniform Conventions

All effect shaders will use consistent uniform names:

```glsl
// Standard uniforms (Shadertoy-compatible)
uniform float iTime;            // Elapsed time in seconds
uniform vec2 iResolution;       // Viewport resolution
uniform vec2 iMouse;            // Mouse/joystick position (-1 to 1)

// Custom uniforms
uniform vec4 iParams;           // 4 adjustable parameters
uniform float iSpeed;           // Animation speed multiplier
uniform int iColorMode;         // Color scheme selector
```

## Terminal Output Mode

For maintaining compatibility with terminal-only environments:

1. Render shader to offscreen framebuffer at terminal resolution
2. Read pixels back to CPU (glReadPixels or PBO)
3. Map brightness/color to ASCII characters
4. Output via existing blessed renderer

**Character mapping example**:
```
Brightness 0.0-0.2 → ' '
Brightness 0.2-0.4 → '.'
Brightness 0.4-0.6 → '░'
Brightness 0.6-0.8 → '▒'
Brightness 0.8-1.0 → '█'
```

## Dependencies

**Required (Phase 1)**:
- `moderngl>=5.8.0` — OpenGL 3.3+ core profile context
- `pygame>=2.5.0` — Already present; provides window/context

**Optional**:
- `numpy>=1.20.0` — For efficient pixel array handling
- `glfw` — Alternative to pygame for window management
- `Pillow>=10.0.0` — Already present; for image/video export

## Open Questions

1. **CPU Fallback**: Do we maintain CPU rendering for systems without GPU?
   - Recommendation: Yes, detect GPU availability at startup

2. **ASCII Output Mode**: Render shader → downsample → terminal?
   - Recommendation: Yes, for terminal-only SSH sessions

3. **Composite Pipeline**: How to handle shader chaining?
   - Recommendation: FBO ping-pong with named render targets

4. **Preset System**: Store shader parameters in same format?
   - Recommendation: Yes, extend existing save slot system

5. **Video Export**: Direct GPU → video or CPU intermediate?
   - Recommendation: GPU readback → ffmpeg pipe for best quality

## File Structure After Implementation

```
atari_style/
├── core/
│   ├── renderer.py           # Terminal renderer (unchanged)
│   ├── input_handler.py      # Input (unchanged)
│   └── gl/
│       ├── __init__.py
│       ├── renderer.py       # GLRenderer base class
│       ├── shader_loader.py  # GLSL loading utilities
│       ├── uniforms.py       # Uniform management
│       └── pipeline.py       # Multi-pass rendering
├── shaders/
│   ├── effects/
│   │   ├── mandelbrot.frag
│   │   ├── plasma.frag
│   │   ├── tunnel.frag
│   │   └── fluid.frag
│   └── post/
│       ├── crt.frag
│       ├── palette.frag
│       └── vignette.frag
└── demos/
    └── visualizers/
        ├── screensaver.py    # CPU version (legacy)
        └── gl_screensaver.py # GPU version (new)
```

## References

- [Shadertoy](https://www.shadertoy.com/) — Inspiration and reference implementations
- [The Book of Shaders](https://thebookofshaders.com/) — GLSL fundamentals
- [moderngl documentation](https://moderngl.readthedocs.io/) — Python OpenGL
- [Inigo Quilez's articles](https://iquilezles.org/articles/) — Advanced shader techniques
