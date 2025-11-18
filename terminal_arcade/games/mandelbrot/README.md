# Mandelbrot Explorer

Interactive fractal viewer for exploring the infinite complexity of the Mandelbrot set.

## Overview

The Mandelbrot set is one of the most famous fractals in mathematics. This interactive explorer lets you navigate through its infinite detail, zoom into fascinating structures, and experience the beauty of mathematical chaos.

## What is the Mandelbrot Set?

The Mandelbrot set is defined by a simple mathematical formula:
- Start with a complex number `c`
- Repeatedly calculate `z = z² + c` (starting with z = 0)
- If `z` stays bounded (doesn't escape to infinity), `c` is in the set

The boundary of this set creates infinitely complex, self-similar patterns at all scales.

## Controls

### Navigation
- **Arrow Keys** or **WASD**: Pan the view in any direction
- **Z**: Zoom in (×0.7)
- **X**: Zoom out (×1.3)

### Visualization
- **C**: Cycle through color palettes (Classic, Fire, Ocean, Monochrome, Rainbow)
- **+/-**: Increase/decrease iteration depth (more detail vs. faster rendering)

### Bookmarks (Jump to Interesting Locations)
- **1**: Overview - Full Mandelbrot set
- **2**: Valley - Detailed valley structure
- **3**: Spiral - Triple spiral formation
- **4**: Seahorse - Classic seahorse valley
- **5**: Triple Spiral - Complex spiral detail
- **6**: Elephant - Elephant valley pattern

### UI Controls
- **H**: Toggle help overlay
- **I**: Toggle coordinate display
- **R**: Reset to overview
- **ESC** or **Q**: Exit to menu

## Color Palettes

### Classic
Blue → Cyan → Green → Yellow → Red → Magenta → White gradient

### Fire
Dark → Red → Yellow → Bright Yellow → White (heat map)

### Ocean
Blue → Cyan → Bright Cyan → Bright Blue → White (underwater)

### Monochrome
Simple grayscale gradient

### Rainbow
Full spectrum: Red → Yellow → Green → Cyan → Blue → Magenta

## Features

- ✓ Real-time rendering with smooth coloring algorithm
- ✓ Infinite zoom capability (limited only by floating-point precision)
- ✓ Adjustable iteration depth (10-500 iterations)
- ✓ Multiple color palette options
- ✓ Preset bookmarks to famous Mandelbrot features
- ✓ Coordinate display for navigation
- ✓ Aspect ratio correction for terminal display
- ✓ Character density mapping for visual depth

## Exploration Tips

1. **Start with Bookmarks**: Press 1-6 to jump to pre-configured interesting locations
2. **Zoom Gradually**: The set reveals new details at every scale - take your time
3. **Adjust Iterations**: When zoomed in deep, increase iterations (+) for more detail
4. **Try Different Palettes**: Different color schemes highlight different features (press C)
5. **Look for Self-Similarity**: Notice how patterns repeat at different scales
6. **Explore the Boundary**: The most interesting structures are near the edge of the set

## Interesting Phenomena to Find

### Mini-Mandelbrots
Tiny copies of the full set appear throughout the fractal - each contains infinite copies of itself!

### Spirals
Look for spiral formations that wind infinitely inward (bookmark 3 and 5)

### Valleys
Deep channels that branch and subdivide into intricate patterns (bookmark 2)

### Seahorse Valley
One of the most famous regions, containing seahorse-like structures (bookmark 4)

## Technical Details

- **Algorithm**: Classic escape-time algorithm with smooth coloring
- **Iteration Range**: 10-500 (user adjustable via +/- keys)
- **Color Mapping**: Smooth gradient using continuous iteration count
- **Rendering**: Character density (· ░ ▒ ▓ █) + color for depth perception
- **Aspect Correction**: Compensates for terminal characters being ~2x taller than wide
- **Frame Rate**: ~30 FPS (rendering time varies with zoom level and iterations)

## Mathematical Background

The Mandelbrot set is defined in the complex plane:
- **Black regions** (█): Points in the set (never escape)
- **Colored regions**: Points outside the set (colored by escape speed)
- **Boundary**: The infinitely complex edge between inside and outside

The formula `z → z² + c` creates feedback that generates chaos theory in action!

## Performance Notes

- **Shallow Zoom**: Fast rendering, lower iteration count sufficient
- **Deep Zoom**: Slower rendering, increase iterations for detail
- **Iterations vs Speed**: More iterations = more detail but slower rendering
- **Optimal Settings**: 50-100 iterations for most zoom levels

## Version History

- **v1.0** - Initial release with 5 color palettes, 6 bookmarks, and smooth coloring

## Fun Facts

- The Mandelbrot set boundary has a fractal dimension of approximately 2
- You can zoom infinitely (limited only by computer precision)
- The set is connected - every point touches every other point
- It was first visualized in 1978 by Robert W. Brooks and Peter Matelski
- Benoît Mandelbrot popularized it in 1980, and it bears his name

---

**Enjoy your journey through infinite mathematical beauty!**
