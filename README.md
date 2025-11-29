# Atari-Style Terminal Games & Demos

A comprehensive collection of terminal-based interactive games, creative tools, and visual demos inspired by classic Atari aesthetics. Features full joystick and keyboard support with ASCII/ANSI graphics.

## Features

### 🎮 Classic Arcade Games

- **Pac-Man** - Maze chase game with 4 ghost AIs (Blinky, Pinky, Inky, Clyde), power-ups, pellet collection, and level progression
- **Galaga** - Space shooter with wave-based enemy formations, dive attacks, UFO bonus ships, and progressive difficulty
- **Grand Prix** - First-person 3D racing with curves, hills, 8 AI opponents, lap timing, and realistic physics
- **Breakout** - Paddle game with ball physics, 5 power-up types, multiple brick types, combo system, and level progression

### 🎨 Creative Tools

- **ASCII Painter** - Full-featured drawing program with:
  - 6 tools (freehand, line, rectangle, circle, flood fill, erase)
  - 4 character palettes (95+ characters: ASCII, box-drawing, blocks, special)
  - 14 colors (standard and bright variants)
  - 3 brush sizes (1x1, 3x3, 5x5)
  - 20-level undo/redo
  - Save/load (.txt and .ansi formats)
  - Grid overlay and help system

### ✨ Visual Demos

- **Starfield** - Enhanced 3D space flight with:
  - 3-layer parallax system (far/mid/near stars)
  - Colored nebula clouds (5 nebulae)
  - Warp tunnel effect (auto-activates at speed > 3x)
  - Asteroid field mode (100 rotating asteroids)
  - Hyperspace jump animation (4-stage sequence)
  - Lateral drift control (X-axis movement)
  - 3 color modes (monochrome, rainbow, speed-based)

- **Screen Saver** - 11 parametric animations (8 base + 3 composites) with real-time joystick control:
  - **Base animations**: Lissajous curves, Spirals, Wave Circles, Plasma effects
  - **Base animations**: Mandelbrot zoomer, Fluid lattice, Particle swarm, Tunnel vision
  - **NEW: Composite animations** - Fusion visuals where one animation modulates another:
    - **Plasma → Lissajous**: Plasma field drives Lissajous curve frequencies
    - **Flux → Spiral**: Fluid wave energy modulates spiral rotation speed
    - **Lissajous → Plasma**: Curve motion drives plasma color cycling
  - 32+ adjustable parameters (4 per animation)
  - Value modulation system for emergent behaviors
  - Help system (press 'H' for parameter descriptions)
  - 4 save slots (hold to save, tap to load)
  - 30-60 FPS rendering

- **Platonic Solids** - Interactive 3D geometry viewer:
  - All 5 Platonic solids (Tetrahedron, Cube, Octahedron, Dodecahedron, Icosahedron)
  - Real-time rotation (X/Y/Z axes)
  - Auto-rotate mode
  - Zoom controls (5-30x range)
  - Wireframe rendering with vertex highlighting

### 🛠️ Utilities

- **Joystick Test** - Connection verification with real-time axis and button display
- **Interactive Menu** - Organized navigation with sections for games, tools, demos, and utilities

## Installation

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Usage

```bash
# Run the main menu
python run.py

# Or use module syntax
python -m atari_style.main
```

### Controls

**Universal Controls**:
- **Arrow Keys** or **WASD** - Navigate menus and control games
- **Enter** or **Space** - Select menu items / Action
- **ESC** or **Q** - Back/Exit
- **Joystick** - Full analog stick and button support

**Game-Specific Controls**:
- **Pac-Man**: Arrow keys/WASD for movement
- **Galaga**: Left/Right for movement, Space/Enter to fire
- **Grand Prix**: Up/Down for speed, Left/Right for steering
- **Breakout**: Left/Right for paddle, Space to launch ball
- **ASCII Painter**: Arrow keys/joystick to move cursor, Space to draw, 1-6 to select tools, H for help

## Tech Stack

- **Python 3.8+**
- **pygame** - Joystick input handling
- **blessed** - Terminal rendering and control

## Project Structure

```
atari_style/
├── core/
│   ├── renderer.py      # Terminal rendering engine (double-buffered)
│   ├── input_handler.py # Unified keyboard/joystick input
│   └── menu.py          # Interactive menu system
├── demos/
│   ├── pacman.py        # Pac-Man maze chase game
│   ├── galaga.py        # Space shooter
│   ├── grandprix.py     # First-person 3D racing
│   ├── breakout.py      # Paddle and ball game
│   ├── ascii_painter.py # ASCII art editor
│   ├── starfield.py     # Enhanced starfield simulation
│   ├── screensaver.py   # Parametric animations
│   ├── platonic_solids.py # 3D geometry viewer
│   └── joystick_test.py # Joystick verification
└── main.py              # Entry point with menu
```

## Development

### Running Individual Demos

```bash
# Games
python -c "from atari_style.demos.pacman import run_pacman; run_pacman()"
python -c "from atari_style.demos.galaga import run_galaga; run_galaga()"
python -c "from atari_style.demos.grandprix import run_grandprix; run_grandprix()"
python -c "from atari_style.demos.breakout import run_breakout; run_breakout()"

# Tools
python -c "from atari_style.demos.ascii_painter import run_ascii_painter; run_ascii_painter()"

# Demos
python -c "from atari_style.demos.starfield import run_starfield; run_starfield()"
python -c "from atari_style.demos.screensaver import run_screensaver; run_screensaver()"
python -c "from atari_style.demos.platonic_solids import run_platonic_solids; run_platonic_solids()"
```

## Features Overview

### Game Highlights

**Pac-Man**: Classic gameplay with BFS pathfinding for ghost AI, 4 distinct ghost personalities, power-up mode (200/400/800/1600 point escalation), wrap-around tunnels, and smooth animations.

**Galaga**: Wave-based formations with dive attack patterns, 3 enemy types (Grunts, Officers, Commanders), bonus UFO ships, progressive difficulty, explosion effects, and accuracy statistics.

**Grand Prix**: Real-time 3D road rendering with perspective projection, 300-segment tracks with dynamic curves and hills, 8 AI opponents with racing line following, off-road penalties, and comprehensive lap timing.

**Breakout**: Physics-based ball reflection (angle depends on paddle hit position), 5 power-up types (Wide Paddle, Multi-Ball, Laser, Slow Ball, Extra Life), 3 brick types (normal, strong, unbreakable), combo scoring system, and 5 level patterns.

### Technical Highlights

- **Double-buffered rendering**: Flicker-free 30-60 FPS animations
- **3D projection**: Perspective projection for starfield, racing, and platonic solids
- **Pathfinding AI**: BFS algorithm for ghost navigation in Pac-Man
- **Physics simulation**: Ball reflection, lateral drift, collision detection
- **Joystick integration**: Full analog control with deadzone handling and button debouncing
- **Undo/redo system**: Stack-based command pattern for ASCII Painter
- **File I/O**: Save/load for ASCII art in .txt and .ansi formats

## Related Projects

This project expands on the concept of terminal-stars with a comprehensive menu system and multiple playable games and demos.

## License

MIT

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

**Made with ❤️ for retro terminal aesthetics**
