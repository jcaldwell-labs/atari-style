# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**atari-style** is a comprehensive collection of terminal-based interactive games, creative tools, and visual demos inspired by classic Atari aesthetics. The project provides playable arcade experiences using ASCII/ANSI terminal graphics with full joystick and keyboard support.

### Implemented Features

The project now includes:

**Classic Arcade Games**:
- Pac-Man - Maze chase game with 4 ghost AIs, power-ups, and level progression
- Galaga - Space shooter with wave-based formations, dive attacks, and UFO bonus ships
- Grand Prix - First-person 3D racing with curves, hills, and AI opponents
- Breakout - Paddle game with physics, power-ups, and multiple brick types

**Creative Tools**:
- ASCII Painter - Full-featured drawing program with 6 tools, undo/redo, and file export

**Visual Demos**:
- Starfield - Enhanced 3D space flight with parallax layers, nebulae, warp tunnel, asteroid mode, and hyperspace jumps
- Screen Saver - 8 parametric animations with real-time joystick control
- Platonic Solids - Interactive 3D viewer for all five Platonic solids

**Utilities**:
- Joystick Test - Connection verification and axis/button testing
- Interactive Menu - Organized navigation with sections for games, tools, demos, and utilities

### Related Project

This project is similar to "terminal-stars" but expanded with a menu system and multiple playable demos.

## Technology Stack

**Language**: Python 3.8+
**Dependencies**:
- `pygame` - Joystick input handling
- `blessed` - Terminal rendering and control

## Setup and Installation

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .

# Run the application
python run.py
# or
python -m atari_style.main
```

**Note**: The project includes a pre-configured virtual environment in `venv/` (already in .gitignore)

## Project Architecture

The project uses a modular architecture with clear separation of concerns:

### Core Modules (`atari_style/core/`)

- **`renderer.py`**: Terminal rendering engine with double buffering
  - `Renderer` class: Handles all terminal output with blessed
  - Buffer-based rendering for flicker-free animation
  - Color support via predefined color constants
  - Drawing primitives: pixels, text, boxes, borders
  - Methods: `set_pixel()`, `draw_text()`, `draw_box()`, `draw_border()`, `render()`

- **`input_handler.py`**: Unified input handling for keyboard and joystick
  - `InputHandler` class: Abstracts keyboard and joystick input
  - Automatic joystick detection and initialization
  - Deadzone handling for analog sticks
  - Input types: UP, DOWN, LEFT, RIGHT, SELECT, BACK, QUIT
  - Methods: `get_input()`, `get_joystick_state()`, `verify_joystick()`

- **`menu.py`**: Interactive menu system
  - `Menu` class: Navigable menu with visual feedback
  - `MenuItem` class: Menu entries with actions and descriptions
  - Keyboard and joystick navigation support
  - Decorative borders and highlighting

### Game Modules (`atari_style/demos/`)

**`pacman.py`**: Pac-Man maze chase game
- Classic maze layout with 240 regular pellets and 4 power pellets
- Player character with 4-directional movement and mouth animation
- 4 ghost enemies with distinct AI personalities:
  - **Blinky** (red): Direct chase - targets player's current position
  - **Pinky** (pink): Ambush - targets ahead of player
  - **Inky** (cyan): Flanking - uses Blinky's position for complex targeting
  - **Clyde** (orange): Shy - chases when far, retreats when close
- BFS pathfinding for ghost navigation
- Mode switching: Chase, Scatter, Frightened, Dead
- Power-up system: Eat ghosts for escalating points (200/400/800/1600)
- Lives system and level progression
- Score tracking with pellet collection
- Wrap-around tunnels on edges
- ~30 FPS gameplay

**`galaga.py`**: Space shooter with wave-based enemies
- Player ship with left/right movement and projectile firing
- 3 enemy types: Grunts (10pts), Officers (20pts), Commanders (40pts)
- Wave-based formation system with side-to-side movement
- Dive attack patterns: Enemies break formation and swoop at player
- Bonus UFO ship: Crosses screen periodically for 100-300 points
- Progressive difficulty: Faster enemies, increased fire rate per wave
- Collision detection for bullets vs ships
- Explosion animations
- Lives system and high score tracking
- Accuracy statistics (shots fired vs hits)
- ~60 FPS rendering

**`grandprix.py`**: First-person 3D racing game
- Real-time 3D road rendering with perspective projection
- Track system: 300 segments with curves and hills
- Player controls: Acceleration, braking, steering
- 8 AI opponent cars with racing line following
- Lateral positioning on road (-1 to 1 range)
- Off-road penalty (grass areas slow you down)
- Lap timing: Current lap, best lap, total time
- 3-lap race completion
- Collision detection with opponents
- Speed display (0-200 km/h) with visual speedometer
- Track progress indicator
- Countdown start sequence
- ~30 FPS for 3D rendering

**`breakout.py`**: Paddle and ball physics game
- Player paddle with left/right movement (analog joystick supported)
- Ball physics: Velocity-based movement with angle reflection
- Paddle hit detection: Reflection angle based on hit position
- Brick field: 8-10 rows with multiple colors and types
  - Normal bricks: 1 hit, 10-70 points by row
  - Strong bricks: 2 hits, 100 points, changes color when damaged
  - Unbreakable bricks: Metal blocks that can't be destroyed
- 5 power-up types (20% drop chance):
  - **P** (Wide Paddle): 2x paddle width for 30 seconds
  - **M** (Multi-Ball): Splits each ball into 3
  - **L** (Laser): Paddle can shoot upward for 20 seconds
  - **S** (Slow Ball): 50% ball speed for 20 seconds
  - **E** (Extra Life): +1 ball
- Combo system: Consecutive brick hits award bonus points
- Level progression with 5 different brick patterns
- Lives system (3 balls)
- Auto-launch timer (3 seconds)
- Ball speed increases with each brick hit (capped)
- Extra life every 10,000 points
- ~60 FPS gameplay

**`ascii_painter.py`**: ASCII art creation tool
- 60x30 character canvas with persistent drawing buffer
- 6 drawing tools:
  - **Freehand**: Paint with selected character
  - **Line**: Bresenham line drawing (2-point)
  - **Rectangle**: Hollow or filled boxes
  - **Circle**: Approximate circle rendering
  - **Flood Fill**: Stack-based fill algorithm (2000 pixel limit)
  - **Erase**: Remove characters
- 4 character palettes:
  - ASCII: All printable characters (95 chars)
  - Box-drawing: ─│┌┐└┘├┤┬┴┼ ═║╔╗╚╝╠╣╦╩╬
  - Blocks: ▀▄█▌▐░▒▓
  - Special: ·•○●◦◉◯⊕⊗⊙◊◇◆⬖⬗★☆
- 14 colors: Standard and bright variants
- 3 brush sizes: 1x1, 3x3 (cross), 5x5 (large cross)
- Undo/Redo: 20-level stack-based history
- File operations:
  - Save as .txt (plain text)
  - Save as .ansi (with ANSI color codes)
  - Auto-save to ~/.atari-style/drawings/
- UI features:
  - Grid overlay toggle (5x5 grid)
  - Cursor with blink animation
  - Real-time position display
  - Help overlay (H key)
  - Message system for feedback
- Full keyboard and joystick support
- ~30 FPS UI updates

### Visual Demo Modules

**`starfield.py`**: Enhanced 3D starfield simulation
- **Parallax layers**: 3 depth layers (far/mid/near) with independent speeds
  - Far layer: 30% stars, dim blue/cyan, 30% speed
  - Mid layer: 40% stars, white, 70% speed
  - Near layer: 30% stars, bright white/cyan, 100% speed
- **Nebula clouds**: 5 colored nebulae (red, magenta, blue, cyan, green)
  - Semi-transparent rendering with density characters (░ ▒)
  - Perlin-noise-like distribution
  - Slower movement than stars (background effect)
  - Toggleable visibility
- **Warp tunnel effect**: Auto-activates at speed > 3x
  - Radial star arrangement into tunnel walls
  - Dynamic tunnel radius based on depth
  - Radial motion streaks
- **Asteroid field mode**: Alternative to stars
  - 100 rotating asteroids with 5 shape characters (◊◇◆⬖⬗)
  - 3x3 character clusters for larger asteroids
  - Depth-based sizing and coloring
- **Hyperspace jump**: 4-stage animation sequence
  - Pause (0.5s) → Flash (0.2s) → Burst (0.5s) → Resume
  - New randomized nebulae after jump
  - Stars burst outward from center during sequence
- **Lateral drift**: X-axis joystick control for side-to-side movement
- **Color modes**: Monochrome (layer-based), Rainbow, Speed-based
- **Motion trails**: Dynamic length based on speed and layer
- ~30 FPS animation

**`screensaver.py`**: Parametric animation collection (unchanged)
- 8 animation modes with 4 adjustable parameters each
- Help system and save slots
- 60 FPS rendering

**`platonic_solids.py`**: Interactive 3D geometry viewer
- All 5 Platonic solids:
  - **Tetrahedron**: 4 vertices, 6 edges, 4 triangular faces
  - **Cube**: 8 vertices, 12 edges, 6 square faces
  - **Octahedron**: 6 vertices, 12 edges, 8 triangular faces
  - **Dodecahedron**: 20 vertices, 30 edges, 12 pentagonal faces
  - **Icosahedron**: 12 vertices, 30 edges, 20 triangular faces
- Real-time 3D rotation around X, Y, Z axes
- Rotation matrix math for smooth transformations
- Perspective projection (3D to 2D)
- Wireframe rendering with directional line characters (─│/\)
- Vertex highlighting with '●' markers
- Auto-rotate mode (toggleable)
- Manual rotation with joystick or keyboard (Q/E for roll)
- Zoom control (+/- keys, range 5-30)
- Cycle through solids with Space or Button 0
- Reset rotation with C key
- HUD displays:
  - Current solid name
  - Vertex/edge/face count
  - Rotation angles (degrees)
  - Auto-rotate status
  - Controls reference
- ~60 FPS rendering

**`joystick_test.py`**: Joystick verification utility (unchanged)
- Visual crosshair and button state display
- Real-time axis readouts

## Development Commands

### Running the Application

```bash
# Main menu launcher
python run.py

# Or using module syntax
python -m atari_style.main
```

### Testing Individual Demos

```bash
# Games
python -c "from atari_style.demos.pacman import run_pacman; run_pacman()"
python -c "from atari_style.demos.galaga import run_galaga; run_galaga()"
python -c "from atari_style.demos.grandprix import run_grandprix; run_grandprix()"
python -c "from atari_style.demos.breakout import run_breakout; run_breakout()"
python -c "from atari_style.demos.flux_control_patterns import run_pattern_flux; run_pattern_flux()"

# Creative Tools
python -c "from atari_style.demos.ascii_painter import run_ascii_painter; run_ascii_painter()"

# Visual Demos
python -c "from atari_style.demos.starfield import run_starfield; run_starfield()"
python -c "from atari_style.demos.screensaver import run_screensaver; run_screensaver()"
python -c "from atari_style.demos.platonic_solids import run_platonic_solids; run_platonic_solids()"

# Utilities
python -c "from atari_style.demos.joystick_test import run_joystick_test; run_joystick_test()"
```

## Adding New Demos

To add a new demo:

1. Create a new file in `atari_style/demos/`
2. Import core modules: `from ..core.renderer import Renderer, Color`
3. Import input: `from ..core.input_handler import InputHandler, InputType`
4. Create a demo class with `__init__()`, `draw()`, `update()`, `handle_input()`, and `run()` methods
5. Create an entry function: `def run_yourDemo():`
6. Add to menu in `atari_style/main.py`:

```python
from .demos.your_demo import run_your_demo

# In main():
menu_items.append(MenuItem(
    "Your Demo Name",
    run_your_demo,
    "Description of your demo"
))
```

## Input Controls

All demos support both keyboard and joystick:

- **Arrow Keys** or **WASD**: Navigation/Movement
- **Enter** or **Space**: Select/Action
- **ESC** or **Q**: Back/Exit
- **Joystick**: Full analog and button support

## Rendering Guidelines

- Terminal characters are not square; use aspect ratio correction for circles (multiply Y by ~0.5)
- Target ~30 FPS with `time.sleep(0.033)` for smooth animation
- Always call `renderer.clear_buffer()` before drawing each frame
- Use `renderer.enter_fullscreen()` and `renderer.exit_fullscreen()` to manage terminal state
- Clean up resources in `finally` blocks

## Performance Considerations

- Rendering is buffer-based to minimize terminal updates
- Use `timeout` parameter in `get_input()` to avoid blocking
- Limit pixel density for complex animations (draw every 2nd pixel)
- pygame event pumping happens in input handler automatically
