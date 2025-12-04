# atari-style Aesthetic Framework

This document defines the visual language that makes something "atari-style." These aren't arbitrary constraints—they're intentional choices that create aesthetic coherence.

## Core Philosophy

**We're not recreating 1977 hardware. We're capturing the spirit.**

The Atari era produced distinctive visuals not from artistic choice, but from working within severe hardware limitations. Those limitations bred creativity. We choose similar constraints deliberately, not from nostalgia, but because constraints create coherent aesthetics.

---

## The Four Principles

### 1. Chunky Over Smooth

Visible pixels and characters have *character*. Smooth gradients and anti-aliasing belong to a different aesthetic.

**Do:**
- Use block characters (█ ▄ ▀) as primary visual elements
- Embrace stepped color transitions
- Let character cells be visible

**Don't:**
- Smooth gradients
- Sub-pixel rendering
- Anti-aliased edges

### 2. Glow Over Flatness

Things should feel like they emit light. CRT phosphors didn't just display—they *glowed*.

**Do:**
- Bright centers with color falloff
- Bloom effects around bright elements
- Color bleeding at edges

**Don't:**
- Flat, uniform fills
- Hard, crisp boundaries
- Perfectly even illumination

### 3. Imperfection Over Precision

Analog systems had noise, jitter, and variation. Perfect digital precision feels sterile.

**Do:**
- Subtle noise in solid colors
- Slight position jitter
- Scan line effects
- Signal interference artifacts

**Don't:**
- Pixel-perfect alignment everywhere
- Mathematically precise curves
- Sterile, clinical visuals

### 4. Immediate Over Polished

Responsive, raw, alive. The visuals should feel like they're being generated in real-time, not pre-rendered.

**Do:**
- React immediately to input
- Show the computation (scan lines, beam traces)
- Embrace temporal artifacts

**Don't:**
- Loading screens for effects
- Pre-composed animations
- Hidden state changes

---

## Color Palettes

### Terminal Colors (16-color ANSI)

The foundation. These map directly to blessed terminal attributes:

```
Standard:        Bright:
  black            bright_black (gray)
  red              bright_red
  green            bright_green
  yellow           bright_yellow
  blue             bright_blue
  magenta          bright_magenta
  cyan             bright_cyan
  white            bright_white
```

### Named Palettes

#### Classic Atari
The original 8-bit feeling.
```
Background: black
Primary:    bright_cyan, bright_green, bright_yellow
Accent:     bright_red, bright_magenta
Text:       white, bright_white
```

#### Plasma
Smooth rainbow gradients for mathematical visualizations.
```
Sequence: blue -> cyan -> green -> yellow -> red -> magenta -> blue
Usage:    Lissajous curves, wave functions, plasma effects
```

#### Midnight
Dark, atmospheric, mysterious.
```
Background: black, blue
Primary:    blue, magenta, bright_magenta
Accent:     cyan, bright_cyan
Highlight:  white
```

#### Forest
Organic, natural, growing.
```
Background: black
Primary:    green, bright_green
Accent:     yellow, cyan
Highlight:  bright_white
```

#### Fire
Intense, dynamic, dangerous.
```
Background: black
Primary:    red, bright_red, yellow
Accent:     bright_yellow, white
Warning:    magenta
```

#### Ocean
Deep, calm, flowing.
```
Background: black, blue
Primary:    blue, cyan, bright_cyan
Accent:     green, bright_blue
Highlight:  white
```

---

## Typography

### Block Characters (Primary)
These are our pixels:
```
█  Full block      - solid fill
▀  Upper half      - half-height top
▄  Lower half      - half-height bottom
▌  Left half       - half-width left
▐  Right half      - half-width right
░  Light shade     - 25% density
▒  Medium shade    - 50% density
▓  Dark shade      - 75% density
```

### Box Drawing (Secondary)
Structural elements:
```
─ │   Horizontal, vertical
┌ ┐   Top corners
└ ┘   Bottom corners
├ ┤   T-junctions (left, right)
┬ ┴   T-junctions (top, bottom)
┼     Cross
═ ║   Double lines
╔ ╗   Double corners
╚ ╝
```

### Symbols (Accents)
Special markers and indicators:
```
●  Filled circle   - cursor, bullet
○  Empty circle    - inactive state
◆  Diamond         - waypoint
★  Star            - score, achievement
·  Middle dot      - subtle trail
•  Bullet          - list item
```

### Line Characters (Wireframes)
For 3D edges and connections:
```
─  Horizontal (mostly horizontal)
│  Vertical (mostly vertical)
/  Forward diagonal
\  Back diagonal
```

---

## Motion Principles

### Frame Rates

| Context | FPS | Rationale |
|---------|-----|-----------|
| Gameplay | 60 | Responsive feel |
| Demos | 30 | "Retro" deliberate motion |
| Video export | 30 | Standard video format |
| GIF preview | 15 | Small file size |

### Animation Patterns

#### Scan Line Progression
Like a CRT beam, animate top-to-bottom:
```
Frame 1: Line 0 updates
Frame 2: Lines 0-1 update
Frame 3: Lines 0-2 update
...
Frame N: Full frame, then restart
```

#### Persistence (Trails)
Bright things leave afterimages:
```
t=0: Element at position, full brightness
t=1: Element moved, previous position at 70%
t=2: Element moved, trail at 50%, 30%
t=3: Trail fades: 30%, 15%, 5%
```

#### Glow Pulse
For emphasis, pulse brightness:
```
Cycle: 1.0 -> 1.2 -> 1.0 -> 0.9 -> 1.0
Period: 0.5-2.0 seconds
```

---

## atari-style Compliance Checklist

Use this checklist when creating new features:

### Colors
- [ ] Uses only 16-color ANSI palette (or GL palette equivalents)
- [ ] Has a defined palette, not random colors
- [ ] Bright variants used for emphasis, not everywhere
- [ ] Black background unless intentionally different

### Typography
- [ ] Block characters for visual elements
- [ ] Box drawing for structure
- [ ] No high-resolution fonts
- [ ] Character spacing respected (no sub-cell positioning)

### Motion
- [ ] Smooth animation (30+ FPS)
- [ ] Responsive to input (< 50ms latency)
- [ ] Trails/persistence for fast-moving elements
- [ ] No jarring transitions

### Effects
- [ ] CRT-style glow where appropriate
- [ ] Scan line awareness (top-to-bottom when relevant)
- [ ] Noise/jitter for organic feel
- [ ] No smooth gradients

### Philosophy Alignment
- [ ] Celebrates terminal constraints, doesn't fight them
- [ ] Interactive/explorable where possible
- [ ] Composable with other tools
- [ ] AI-readable code

---

## Anti-Patterns

What is **NOT** atari-style:

| Anti-Pattern | Why | Instead |
|--------------|-----|---------|
| Smooth gradients | Too modern, loses chunky feel | Stepped color bands |
| High-resolution detail | Betrays character-cell aesthetic | Block-level detail |
| Modern UI chrome | Flat design is a different era | Box-drawing frames |
| Photorealism | Wrong medium entirely | Symbolic representation |
| Excessive colors | 16 colors is the constraint | Palette discipline |
| Perfect geometry | Too precise, loses analog feel | Deliberate imperfection |

---

## Implementation Notes

### Terminal (blessed)

Colors are string attributes:
```python
from atari_style.core.renderer import Color

renderer.set_pixel(x, y, '█', Color.BRIGHT_CYAN)
renderer.draw_text(x, y, "SCORE", Color.YELLOW)
```

### GL Shaders

Palettes use cosine gradients (Inigo Quilez technique):
```glsl
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}
```

### Video Export

Maintain aesthetic in exports:
- Use CRF 18-23 for quality
- Preserve color accuracy (no aggressive compression)
- 30 FPS for demos, 60 FPS for gameplay
- Consider scan line overlay for extra authenticity

---

## References

- [Atari 2600 Hardware Specifications](https://en.wikipedia.org/wiki/Television_Interface_Adaptor)
- [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Inigo Quilez - Cosine Palettes](https://iquilezles.org/articles/palettes/)
- [CRT Simulation Techniques](https://www.shadertoy.com/view/XsjSzR)

---

*This is a living document. As atari-style evolves, so should this framework.*

Last updated: 2025-12-03
