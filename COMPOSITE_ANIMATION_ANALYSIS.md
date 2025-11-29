# Composite Animation Analysis

## Overview

This document analyzes the potential for creating composite/fusion screen saver demos where one animation's output can drive or modulate another animation's parameters.

## Existing Animations with Modulation Potential

### 1. Lissajous Curve
- **Parameters**: `a` (freq_x), `b` (freq_y), `delta` (phase), `points`
- **Modulation Sources**: Position data from curve points
- **Modulation Targets**: Can drive frequencies in other animations
- **Value Sweeps**: Continuous X/Y position values (-1 to 1 normalized)

### 2. Plasma
- **Parameters**: `freq_x`, `freq_y`, `freq_diag`, `freq_radial`
- **Modulation Sources**: Per-pixel value field (-1 to 1)
- **Modulation Targets**: Can drive color, intensity, or spatial parameters
- **Value Sweeps**: Smooth gradient across entire screen

### 3. Fluid Lattice (Flux)
- **Parameters**: `rain_rate`, `wave_speed`, `drop_strength`, `damping`
- **Modulation Sources**: Per-cell height values (wave amplitude)
- **Modulation Targets**: Can drive rotation, scale, position offsets
- **Value Sweeps**: Dynamic, localized wave patterns

### 4. Spiral
- **Parameters**: `num_spirals`, `rotation_speed`, `tightness`, `radius_scale`
- **Modulation Sources**: Radial distance, angular position
- **Modulation Targets**: Good for driving circular/rotational effects
- **Value Sweeps**: Smooth radial gradients

### 5. Tunnel Vision
- **Parameters**: `depth_speed`, `rotation_speed`, `tunnel_size`, `color_cycle_speed`
- **Modulation Sources**: Depth and angle values
- **Modulation Targets**: Can drive perspective effects
- **Value Sweeps**: Depth-based gradients

## Composite Animation Possibilities

### Category 1: Value Modulation
**Concept**: One animation's output values drive another's parameters in real-time

#### A. Plasma → Lissajous
- Plasma value at center point drives Lissajous frequencies
- Creates evolving curve shapes synchronized to plasma waves
- **Implementation**: Sample plasma value, map to freq_x/freq_y range
- **Visual Effect**: Lissajous morphs as plasma undulates

#### B. Flux → Spiral
- Fluid lattice height drives spiral rotation speed
- Wave peaks cause faster spinning, valleys slow down
- **Implementation**: Average fluid values, map to rotation_speed
- **Visual Effect**: Spiral pulses with wave rhythm

#### C. Lissajous → Plasma
- Curve position drives plasma color cycling speed
- **Implementation**: Track curve center of mass, modulate color_cycle
- **Visual Effect**: Plasma colors dance with curve motion

### Category 2: Spatial Blending
**Concept**: Multiple animations rendered simultaneously with alpha blending or masking

#### D. Plasma + Tunnel Vision (Blend)
- Plasma provides color/texture for tunnel walls
- Tunnel geometry masks plasma pattern
- **Implementation**: Render both, blend based on tunnel depth
- **Visual Effect**: Textured tunnel with organic plasma walls

#### E. Particle Swarm + Fluid Lattice
- Particles leave trails in fluid lattice
- Fluid waves influence particle movement
- **Implementation**: Particles create drops, fluid values bias velocity
- **Visual Effect**: Interactive swarm with wave feedback

#### F. Mandelbrot + Lissajous
- Lissajous overlaid on Mandelbrot zoom
- Curve follows interesting Mandelbrot features
- **Implementation**: Layer curve on fractal, cursor follows deep regions
- **Visual Effect**: Guided tour through fractal landscape

### Category 3: Temporal Synchronization
**Concept**: Multiple animations share time/phase for synchronized motion

#### G. Dual Lissajous (Harmonic)
- Two Lissajous curves with harmonic frequency ratios
- Shared phase creates interference patterns
- **Implementation**: Run two curves with related frequencies
- **Visual Effect**: Moiré patterns and beating frequencies

#### H. Spiral + Wave Circles (Concentric)
- Spiral arms match wave circle positions
- Synchronized rotation creates pinwheel effect
- **Implementation**: Lock rotation phases
- **Visual Effect**: Nested rotating patterns

#### I. Triple Plasma (RGB Channels)
- Three plasma animations, one per color channel
- Phase-shifted for psychedelic effect
- **Implementation**: Render R/G/B separately with time offsets
- **Visual Effect**: Chromatic plasma with depth

### Category 4: Feedback Systems
**Concept**: Animations influence each other bidirectionally

#### J. Flux ⇄ Particle Swarm
- Particles drop into fluid (create waves)
- Fluid waves push particles (add velocity)
- **Implementation**: Bidirectional force coupling
- **Visual Effect**: Emergent complex behavior

#### K. Plasma ⇄ Tunnel
- Plasma values modulate tunnel size
- Tunnel depth modulates plasma frequency
- **Implementation**: Cross-parameter mapping
- **Visual Effect**: Breathing, organic tunnel

## Implementation Architecture

### Base Class Design

```python
class CompositeAnimation(ParametricAnimation):
    """Base class for composite animations."""
    
    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.animations = []  # Child animations
        self.modulation_mode = "value"  # value, spatial, temporal, feedback
        
    def sample_value(self, animation, x=None, y=None):
        """Sample output value from child animation."""
        pass
        
    def apply_modulation(self, source, target, mapping):
        """Apply modulation from source to target."""
        pass
```

### Modulation Interface

```python
class ModulationSource:
    """Interface for animations that can modulate others."""
    
    def get_value_at(self, x, y, t):
        """Get normalized value (-1 to 1) at position and time."""
        raise NotImplementedError
        
    def get_global_value(self, t):
        """Get global scalar value for the animation."""
        raise NotImplementedError
```

## Priority Implementations

### Phase 1: Value Modulation (Easiest, Most Impact)
1. **Plasma → Lissajous** - Most visually interesting
2. **Flux → Spiral** - Good demonstration of rhythm
3. **Lissajous → Plasma** - Closes the loop

### Phase 2: Spatial Blending
4. **Plasma + Tunnel** - Textured surfaces
5. **Particle + Flux** - Interactive demo

### Phase 3: Advanced
6. **Dual Lissajous** - Mathematical beauty
7. **Triple Plasma RGB** - Psychedelic effect

## GitHub Issues to Create

### Issue 1: Value Modulation System
**Title**: Implement value modulation for composite animations
**Labels**: enhancement, animation
**Description**: 
- Add ModulationSource interface to base animation class
- Implement value sampling for Plasma, Flux, Lissajous
- Create mapping functions (linear, exponential, sigmoid)
- Add 3 proof-of-concept composite animations

### Issue 2: Spatial Blending Renderer
**Title**: Add spatial blending support to renderer
**Labels**: enhancement, renderer
**Description**:
- Extend Renderer with alpha blending capability
- Add layer management system
- Implement masking operations
- Create Plasma+Tunnel demo

### Issue 3: Temporal Sync Framework
**Title**: Synchronization framework for multi-animation timing
**Labels**: enhancement, architecture
**Description**:
- Shared time source for animations
- Phase locking mechanism
- Harmonic ratio calculator
- Dual Lissajous demo

### Issue 4: Interactive Composite Demo
**Title**: Interactive composite animation selector
**Labels**: enhancement, ui
**Description**:
- Menu system to select composite mode
- Live switching between composites
- Save/load composite configurations
- Help text for each composite type

## Testing Strategy

1. **Unit Tests**: Test modulation value ranges (-1 to 1)
2. **Visual Tests**: Screenshot comparison for composites
3. **Performance Tests**: Ensure 60 FPS with composites
4. **Integration Tests**: Menu navigation to composites

## Documentation Updates

1. Update README with composite animations section
2. Add COMPOSITE_CONTROLS.md for new interactions
3. Update ANIMATIONS-VISUAL-GUIDE.md with composite examples
4. Add composite demos to main menu

## Performance Considerations

- Composites may run slower due to multiple renders
- Target 30 FPS minimum for composites
- Add quality settings (skip pixels for performance)
- Profile and optimize hot paths
