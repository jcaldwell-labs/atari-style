# GitHub Issues for Composite Screen Saver Implementation

This document contains detailed issue descriptions ready to be created on GitHub for implementing composite/fusion screen saver animations.

---

## Issue #1: Value Modulation System for Composite Animations

**Title**: Implement value modulation system for composite animations

**Labels**: `enhancement`, `animation`, `good first issue`

**Description**:

### Overview
Create a system that allows one animation's output values to drive/modulate another animation's parameters in real-time. This enables dynamic, evolving visuals where animations influence each other.

### Motivation
The parametric animations (Plasma, Flux, Lissajous) have interesting value sweeps that create illusions of motion and rotation. By letting one animation modulate another, we can create emergent visual behaviors that are more interesting than the sum of their parts.

### Requirements

#### 1. ModulationSource Interface
Add to base `ParametricAnimation` class:

```python
def get_value_at(self, x: int, y: int, t: float) -> float:
    """Get normalized value (-1.0 to 1.0) at screen position (x, y) and time t.
    
    Returns:
        float: Normalized value representing animation state at this point
    """
    return 0.0

def get_global_value(self, t: float) -> float:
    """Get global scalar value for the entire animation at time t.
    
    Returns:
        float: Normalized value (-1.0 to 1.0) representing overall animation state
    """
    return 0.0
```

#### 2. Implement for Key Animations

**PlasmaAnimation**:
- `get_value_at(x, y, t)`: Return the plasma value at that pixel
- `get_global_value(t)`: Return average plasma value across screen

**FluidLattice**:
- `get_value_at(x, y, t)`: Return the wave height at that lattice cell
- `get_global_value(t)`: Return average wave height

**LissajousCurve**:
- `get_value_at(x, y, t)`: Return distance to nearest curve point (inverse)
- `get_global_value(t)`: Return current phase angle

#### 3. CompositeAnimation Base Class

```python
class CompositeAnimation(ParametricAnimation):
    """Animation that combines multiple child animations with modulation."""
    
    def __init__(self, renderer: Renderer, source: ParametricAnimation, target: ParametricAnimation):
        super().__init__(renderer)
        self.source = source  # Provides modulation values
        self.target = target  # Receives modulation
        self.modulation_strength = 1.0  # 0.0 = no modulation, 1.0 = full
        self.modulation_mapping = "linear"  # linear, quadratic, sine
        
    def map_value(self, value: float, min_out: float, max_out: float) -> float:
        """Map normalized value to output range using selected mapping."""
        if self.modulation_mapping == "linear":
            return min_out + (value + 1.0) * 0.5 * (max_out - min_out)
        elif self.modulation_mapping == "quadratic":
            # ... implementation
        elif self.modulation_mapping == "sine":
            # ... implementation
```

#### 4. Proof-of-Concept Composites

Implement these three demonstrations:

**A. PlasmaLissajous** - Plasma modulates Lissajous frequencies
```python
class PlasmaLissajous(CompositeAnimation):
    """Lissajous curve with frequencies driven by plasma field."""
    
    def draw(self, t: float):
        # Sample plasma at center
        plasma_value = self.source.get_global_value(t)
        
        # Modulate Lissajous frequencies
        self.target.a = self.map_value(plasma_value, 2.0, 6.0)
        self.target.b = self.map_value(-plasma_value, 2.0, 6.0)
        
        # Draw the modulated Lissajous
        self.target.draw(t)
```

**B. FluxSpiral** - Fluid lattice modulates spiral rotation
```python
class FluxSpiral(CompositeAnimation):
    """Spiral with rotation driven by fluid wave energy."""
    
    def draw(self, t: float):
        # Get average fluid energy
        flux_value = self.source.get_global_value(t)
        
        # Modulate rotation speed
        self.target.rotation_speed = self.map_value(flux_value, 0.5, 3.0)
        
        # Draw the modulated spiral
        self.target.draw(t)
```

**C. LissajousPlasma** - Lissajous modulates plasma colors
```python
class LissajousPlasma(CompositeAnimation):
    """Plasma with color cycling driven by Lissajous motion."""
    
    def draw(self, t: float):
        # Get Lissajous phase
        liss_value = self.source.get_global_value(t)
        
        # Modulate plasma frequencies
        self.target.freq_x = self.map_value(liss_value, 0.05, 0.15)
        self.target.freq_y = self.map_value(-liss_value, 0.05, 0.15)
        
        # Draw the modulated plasma
        self.target.draw(t)
```

### Implementation Checklist
- [ ] Add `get_value_at()` and `get_global_value()` to `ParametricAnimation`
- [ ] Implement modulation interface for `PlasmaAnimation`
- [ ] Implement modulation interface for `FluidLattice`
- [ ] Implement modulation interface for `LissajousCurve`
- [ ] Create `CompositeAnimation` base class
- [ ] Implement `PlasmaLissajous` composite
- [ ] Implement `FluxSpiral` composite
- [ ] Implement `LissajousPlasma` composite
- [ ] Add composites to ScreenSaver animation list
- [ ] Create unit tests for value sampling
- [ ] Create visual tests (screenshots)
- [ ] Update documentation

### Testing
```python
def test_plasma_value_range():
    """Test that plasma values are in [-1, 1] range."""
    plasma = PlasmaAnimation(renderer)
    for x in range(0, 100, 10):
        for y in range(0, 50, 10):
            value = plasma.get_value_at(x, y, 0.0)
            assert -1.0 <= value <= 1.0

def test_composite_modulation():
    """Test that modulation affects target parameters."""
    composite = PlasmaLissajous(renderer, plasma, lissajous)
    initial_freq = composite.target.a
    composite.draw(1.0)
    assert composite.target.a != initial_freq  # Should be modulated
```

### Acceptance Criteria
- All three composite animations run at 30+ FPS
- Modulation values stay in valid parameter ranges
- Visual output shows clear modulation effect
- Tests pass and achieve >80% coverage
- Documentation updated with examples

---

## Issue #2: Spatial Blending Renderer for Layered Animations

**Title**: Add spatial blending support for layered composite animations

**Labels**: `enhancement`, `renderer`, `architecture`

**Description**:

### Overview
Extend the Renderer to support alpha blending and masking operations, enabling multiple animations to be composited spatially (layered on top of each other).

### Motivation
Some composite effects require rendering multiple animations simultaneously and blending them together, such as texturing tunnel walls with plasma or having particles interact with fluid surfaces.

### Requirements

#### 1. Multi-Layer Buffer System

Extend `Renderer` class:

```python
class Renderer:
    # ... existing code ...
    
    def __init__(self):
        # ... existing init ...
        self.layers = {}  # Dict of layer_id -> buffer
        self.current_layer = "default"
        
    def push_layer(self, layer_id: str):
        """Create and switch to a new drawing layer."""
        if layer_id not in self.layers:
            self.layers[layer_id] = [[(' ', None) for _ in range(self.width)] 
                                      for _ in range(self.height)]
        self.current_layer = layer_id
        
    def pop_layer(self):
        """Return to default layer."""
        self.current_layer = "default"
        
    def blend_layers(self, layer1: str, layer2: str, mode: str = "alpha"):
        """Blend two layers together.
        
        Args:
            layer1: Bottom layer
            layer2: Top layer
            mode: Blending mode ("alpha", "add", "multiply", "mask")
        """
        # Implementation of blending logic
        pass
```

#### 2. Alpha Blending Modes

Support these blending modes:

- **Alpha**: Standard transparency blend
- **Add**: Additive blending (colors add together)
- **Multiply**: Colors multiply (darkening effect)
- **Mask**: Layer2 only shows where layer1 has content

#### 3. Spatial Composite Animations

**PlasmaTexturedTunnel**:
```python
class PlasmaTexturedTunnel(CompositeAnimation):
    """Tunnel vision with plasma-textured walls."""
    
    def draw(self, t: float):
        # Render plasma to layer 0
        self.renderer.push_layer("plasma")
        self.plasma.draw(t)
        self.renderer.pop_layer()
        
        # Render tunnel to layer 1
        self.renderer.push_layer("tunnel")
        self.tunnel.draw(t)
        self.renderer.pop_layer()
        
        # Blend: tunnel geometry masks plasma texture
        self.renderer.blend_layers("plasma", "tunnel", mode="mask")
```

**ParticleFluidInteraction**:
```python
class ParticleFluidInteraction(CompositeAnimation):
    """Particles create ripples in fluid lattice."""
    
    def update(self, dt: float):
        # Update particles
        self.particles.update(dt)
        
        # Particles drop into fluid
        for particle in self.particles.particles:
            if particle['active']:
                x = int(particle['x'] / 2)
                y = int(particle['y'])
                if 0 <= x < self.fluid.width and 0 <= y < self.fluid.height:
                    self.fluid.current[y][x] += 3.0  # Create drop
        
        # Fluid pushes particles
        for particle in self.particles.particles:
            if particle['active']:
                x = int(particle['x'] / 2)
                y = int(particle['y'])
                if 0 <= x < self.fluid.width and 0 <= y < self.fluid.height:
                    force = self.fluid.current[y][x]
                    particle['vx'] += force * 0.1
                    particle['vy'] += force * 0.05
        
        self.fluid.update(dt)
    
    def draw(self, t: float):
        # Draw fluid
        self.renderer.push_layer("fluid")
        self.fluid.draw(t)
        self.renderer.pop_layer()
        
        # Draw particles on top
        self.renderer.push_layer("particles")
        self.particles.draw(t)
        self.renderer.pop_layer()
        
        # Alpha blend
        self.renderer.blend_layers("fluid", "particles", mode="alpha")
```

### Implementation Checklist
- [ ] Add layer system to Renderer
- [ ] Implement `push_layer()` and `pop_layer()`
- [ ] Implement alpha blending mode
- [ ] Implement additive blending mode
- [ ] Implement multiply blending mode
- [ ] Implement mask blending mode
- [ ] Create `PlasmaTexturedTunnel` composite
- [ ] Create `ParticleFluidInteraction` composite
- [ ] Performance optimization (avoid full-screen blends if possible)
- [ ] Add tests for blending operations
- [ ] Update documentation

### Performance Considerations
- Blending full screen at 60 FPS may be slow
- Consider partial blending (only changed regions)
- Add quality setting to skip pixels if needed
- Profile and optimize hot paths

### Acceptance Criteria
- Layer system works correctly with multiple buffers
- All blending modes produce expected visual output
- Performance stays above 30 FPS for two-layer composites
- Tests verify blending math is correct

---

## Issue #3: Temporal Synchronization Framework

**Title**: Add temporal synchronization framework for harmonic animations

**Labels**: `enhancement`, `animation`, `advanced`

**Description**:

### Overview
Create a synchronization framework that allows multiple animations to share timing and phase information, enabling harmonic relationships and interference patterns.

### Motivation
Mathematical beauty emerges when animations are phase-locked with harmonic ratios. This creates moiré patterns, beating frequencies, and emergent rhythms.

### Requirements

#### 1. SharedTimeSource

```python
class SharedTimeSource:
    """Shared time and phase source for synchronized animations."""
    
    def __init__(self):
        self.master_time = 0.0
        self.phase_offsets = {}
        
    def register_animation(self, anim_id: str, phase_offset: float = 0.0):
        """Register an animation with optional phase offset."""
        self.phase_offsets[anim_id] = phase_offset
        
    def get_time(self, anim_id: str) -> float:
        """Get time for a specific animation including phase offset."""
        return self.master_time + self.phase_offsets.get(anim_id, 0.0)
        
    def update(self, dt: float):
        """Update master time."""
        self.master_time += dt
```

#### 2. Harmonic Ratio Calculator

```python
class HarmonicCalculator:
    """Calculate harmonic frequency ratios."""
    
    @staticmethod
    def get_harmonic_ratio(fundamental: float, harmonic: int) -> float:
        """Get frequency ratio for a harmonic number."""
        return fundamental * harmonic
        
    @staticmethod
    def get_subharmonic_ratio(fundamental: float, divisor: int) -> float:
        """Get frequency ratio for a subharmonic."""
        return fundamental / divisor
```

#### 3. Synchronized Composite Animations

**DualLissajous**:
```python
class DualLissajous(CompositeAnimation):
    """Two Lissajous curves with harmonic frequency relationship."""
    
    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.time_source = SharedTimeSource()
        self.liss1 = LissajousCurve(renderer)
        self.liss2 = LissajousCurve(renderer)
        
        # Set up harmonic relationship (2:3 ratio)
        self.liss1.a = 2.0
        self.liss1.b = 3.0
        self.liss2.a = 3.0
        self.liss2.b = 2.0
        
        # Phase offset creates interference pattern
        self.time_source.register_animation("liss1", 0.0)
        self.time_source.register_animation("liss2", math.pi / 4)
    
    def draw(self, t: float):
        # Draw both curves with synchronized time
        t1 = self.time_source.get_time("liss1")
        t2 = self.time_source.get_time("liss2")
        
        self.renderer.push_layer("liss1")
        self.liss1.draw(t1)
        self.renderer.pop_layer()
        
        self.renderer.push_layer("liss2")
        self.liss2.draw(t2)
        self.renderer.pop_layer()
        
        # Blend with different colors for each curve
        self.renderer.blend_layers("liss1", "liss2", mode="add")
```

**TriplePlasmaRGB**:
```python
class TriplePlasmaRGB(CompositeAnimation):
    """Three plasma animations, one per RGB channel, phase-shifted."""
    
    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.time_source = SharedTimeSource()
        self.plasma_r = PlasmaAnimation(renderer)
        self.plasma_g = PlasmaAnimation(renderer)
        self.plasma_b = PlasmaAnimation(renderer)
        
        # Phase shift by 120 degrees (2π/3) for RGB
        self.time_source.register_animation("red", 0.0)
        self.time_source.register_animation("green", 2 * math.pi / 3)
        self.time_source.register_animation("blue", 4 * math.pi / 3)
    
    def draw(self, t: float):
        # Each plasma contributes to one color channel
        # This requires renderer support for per-channel blending
        # (Advanced implementation)
        pass
```

### Implementation Checklist
- [ ] Create `SharedTimeSource` class
- [ ] Create `HarmonicCalculator` utility
- [ ] Implement `DualLissajous` composite
- [ ] Implement phase locking mechanism
- [ ] Add frequency ratio controls
- [ ] Create visual tests showing interference patterns
- [ ] Update documentation with harmonic theory

### Mathematical Background
Include documentation on:
- Harmonic series (1:2:3:4...)
- Interference patterns (beating frequencies)
- Phase relationships (0°, 90°, 180°)
- Moiré patterns from overlapping curves

### Acceptance Criteria
- DualLissajous shows clear interference patterns
- Phase offsets produce expected visual shifts
- Harmonic ratios create stable patterns
- Documentation explains the mathematics

---

## Issue #4: Interactive Composite Animation Selector

**Title**: Add interactive menu for selecting and configuring composite animations

**Labels**: `enhancement`, `ui`, `user-experience`

**Description**:

### Overview
Create a user-friendly interface for selecting composite animation modes, switching between them, and saving/loading configurations.

### Motivation
Users need an easy way to explore the various composite animations without editing code. The interface should match the existing screen saver UX.

### Requirements

#### 1. Composite Mode Selection

Add to ScreenSaver class:

```python
class ScreenSaver:
    def __init__(self):
        # ... existing code ...
        
        # Composite animations (index 8+)
        self.composite_animations = [
            PlasmaLissajous(self.renderer, plasma, lissajous),
            FluxSpiral(self.renderer, flux, spiral),
            LissajousPlasma(self.renderer, lissajous, plasma),
            PlasmaTexturedTunnel(self.renderer, plasma, tunnel),
            ParticleFluidInteraction(self.renderer, particles, fluid),
            DualLissajous(self.renderer),
        ]
        
        self.composite_names = [
            "Plasma → Lissajous",
            "Flux → Spiral",
            "Lissajous → Plasma",
            "Plasma Tunnel",
            "Particle Fluid",
            "Dual Lissajous",
        ]
        
        self.all_animations = self.animations + self.composite_animations
        self.all_names = self.animation_names + self.composite_names
```

#### 2. UI Enhancements

**Status Bar**:
```
[Mode: Plasma → Lissajous] [Source: Plasma freq_x=0.12] [Target: Lissajous a=4.2] [FPS: 58]
```

**Help Text for Composites**:
```
COMPOSITE: Plasma → Lissajous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This composite uses the plasma field
value to drive the Lissajous curve
frequencies in real-time.

CONTROLS:
  TAB: Toggle composite/simple mode
  1-4: Adjust modulation strength
  M:   Cycle modulation mapping
```

#### 3. Configuration Persistence

Extend save slot system:

```python
def save_composite_state(self, slot: int):
    """Save composite configuration to slot."""
    state = {
        'mode': 'composite',
        'animation_index': self.current_animation,
        'modulation_strength': self.current_composite.modulation_strength,
        'modulation_mapping': self.current_composite.modulation_mapping,
        'source_params': {...},
        'target_params': {...},
    }
    self.save_slots[slot] = state
```

#### 4. Live Mode Switching

```python
def toggle_composite_mode(self):
    """Switch between simple and composite animation modes."""
    if self.current_animation < len(self.animations):
        # Switch to corresponding composite if available
        if self.current_animation + len(self.animations) < len(self.all_animations):
            self.current_animation += len(self.animations)
    else:
        # Switch back to simple mode
        self.current_animation -= len(self.animations)
```

### Implementation Checklist
- [ ] Add composite animations to ScreenSaver
- [ ] Implement mode switching (TAB key)
- [ ] Add modulation strength controls
- [ ] Add modulation mapping cycle
- [ ] Extend save/load for composite configs
- [ ] Update help system with composite descriptions
- [ ] Add visual indicators for composite mode
- [ ] Test all keyboard shortcuts
- [ ] Update documentation

### UI Mockup

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                       COMPOSITE SCREEN SAVER                                ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║                    [Animated Plasma → Lissajous Display]                   ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║ Mode: Plasma → Lissajous [COMPOSITE] │ Modulation: 75% [Linear]  │ FPS: 58║
║ Source: Plasma freq_x=0.12 freq_y=0.10 │ Target: Lissajous a=4.2 b=3.1    ║
╠═════════════════════════════════════════════════════════════════════════════╣
║ TAB: Toggle Mode │ ← → : Switch │ ↑ ↓ : Params │ M: Mapping │ H: Help    ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

### Acceptance Criteria
- All composites accessible from menu
- Mode switching works smoothly
- Save/load preserves composite state
- Help text is clear and useful
- UI is responsive and intuitive

---

## Issue #5: Performance Optimization for Composite Rendering

**Title**: Optimize composite animation rendering for 60 FPS

**Labels**: `performance`, `optimization`, `enhancement`

**Description**:

### Overview
Ensure composite animations run at acceptable framerates (30-60 FPS) through profiling and optimization.

### Motivation
Rendering multiple animations simultaneously can be CPU-intensive. Need to identify bottlenecks and optimize hot paths.

### Requirements

#### 1. Profiling Infrastructure

```python
import cProfile
import pstats

def profile_composite(composite, duration=10.0):
    """Profile a composite animation for performance analysis."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run animation
    start = time.time()
    frames = 0
    while time.time() - start < duration:
        composite.draw(time.time())
        composite.update(1/60)
        frames += 1
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print(f"\nRendered {frames} frames in {duration}s = {frames/duration:.1f} FPS")
```

#### 2. Optimization Techniques

**Spatial Sampling**:
```python
# Instead of every pixel, sample every Nth pixel
for y in range(0, height, 2):  # Skip every other row
    for x in range(0, width, 2):  # Skip every other column
        value = plasma.get_value_at(x, y, t)
        # Fill in skipped pixels with same value
```

**Caching**:
```python
class CachedComposite(CompositeAnimation):
    def __init__(self, renderer):
        super().__init__(renderer)
        self.value_cache = {}
        self.cache_lifetime = 0.1  # Seconds
        self.last_cache_time = 0.0
    
    def get_cached_value(self, t):
        if t - self.last_cache_time > self.cache_lifetime:
            self.value_cache = {}
            self.last_cache_time = t
        return self.value_cache
```

**Lazy Evaluation**:
```python
# Don't update parts of the screen that haven't changed
if not self.source.has_changed(region):
    return  # Skip redraw
```

#### 3. Quality Settings

```python
class PerformanceSettings:
    QUALITY_LOW = {
        'sample_rate': 4,  # Every 4th pixel
        'update_rate': 2,  # Update every 2nd frame
        'blend_quality': 'fast',
    }
    QUALITY_MEDIUM = {
        'sample_rate': 2,
        'update_rate': 1,
        'blend_quality': 'normal',
    }
    QUALITY_HIGH = {
        'sample_rate': 1,
        'update_rate': 1,
        'blend_quality': 'best',
    }
```

### Implementation Checklist
- [ ] Add profiling utilities
- [ ] Profile all composite animations
- [ ] Identify performance bottlenecks
- [ ] Implement spatial sampling optimization
- [ ] Implement value caching
- [ ] Add quality settings
- [ ] Test FPS at different quality levels
- [ ] Document performance characteristics

### Performance Targets
- **High Quality**: 60 FPS on modern hardware
- **Medium Quality**: 45 FPS
- **Low Quality**: 30 FPS (minimum acceptable)

### Acceptance Criteria
- All composites run at target FPS
- Quality settings work as expected
- Profiling data shows improvements
- Documentation includes performance notes

---

## Implementation Priority

### Phase 1 (Week 1): Foundation
1. Issue #1: Value Modulation System ⭐ **Start here**
   - Most impactful
   - Relatively simple
   - Enables further work

### Phase 2 (Week 2): Visual Enhancement
2. Issue #2: Spatial Blending Renderer
   - Builds on Phase 1
   - Unlocks new composite types

### Phase 3 (Week 3): Advanced Features
3. Issue #3: Temporal Synchronization
   - Mathematical beauty
   - Advanced users

4. Issue #4: Interactive Selector
   - Makes everything accessible
   - User experience polish

### Phase 4 (Week 4): Optimization
5. Issue #5: Performance Optimization
   - Ensure quality
   - Production ready

---

## Testing Strategy Across All Issues

### Unit Tests
- Value range validation (all values in [-1, 1])
- Parameter mapping correctness
- Blending math verification
- Time synchronization accuracy

### Integration Tests
- Composite animations run without crashes
- Menu navigation works
- Save/load preserves state
- All keyboard shortcuts function

### Visual Tests
- Screenshot comparison (before/after)
- Video recording of animations
- Side-by-side reference images

### Performance Tests
- FPS benchmarking
- Memory profiling
- CPU usage monitoring

---

## Documentation Requirements

### For Each Issue
- [ ] Update README.md with new features
- [ ] Add examples to ANIMATIONS-VISUAL-GUIDE.md
- [ ] Create COMPOSITE_CONTROLS.md
- [ ] Update help text in application
- [ ] Add code comments and docstrings
- [ ] Include mathematical explanations where relevant

---

## Success Metrics

By the end of implementation:
- ✅ 6+ composite animations available
- ✅ All running at 30+ FPS
- ✅ Full test coverage (>80%)
- ✅ Complete documentation
- ✅ Positive user feedback
- ✅ No regression in existing features
