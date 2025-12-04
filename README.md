# Atari-Style Terminal Games & Demos

A creative pipeline for terminal-native parametric visualization, built through human-AI collaboration, following Unix philosophy principles.

> **atari-style** celebrates terminal aesthetics as a medium, not a limitation. We create tools that treat parameter spaces as territories to explore, compose freely with other tools via text streams, and teach through interactive play.

Features classic arcade games, creative tools, and GPU-accelerated visual demos with full joystick and keyboard support.

## Features

### Classic Arcade Games

- **Pac-Man** - Maze chase game with 4 ghost AIs (Blinky, Pinky, Inky, Clyde), power-ups, pellet collection, and level progression
- **Galaga** - Space shooter with wave-based enemy formations, dive attacks, UFO bonus ships, and progressive difficulty
- **Grand Prix** - First-person 3D racing with curves, hills, 8 AI opponents, lap timing, and realistic physics
- **Breakout** - Paddle game with ball physics, 5 power-up types, multiple brick types, combo system, and level progression

### Creative Tools

- **ASCII Painter** - Full-featured drawing program with:
  - 6 tools (freehand, line, rectangle, circle, flood fill, erase)
  - 4 character palettes (95+ characters: ASCII, box-drawing, blocks, special)
  - 14 colors (standard and bright variants)
  - 3 brush sizes (1x1, 3x3, 5x5)
  - 20-level undo/redo
  - Save/load (.txt and .ansi formats)
  - Grid overlay and help system

### Visual Demos

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
  - **Composite animations** - Fusion visuals where one animation modulates another:
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

### Utilities

- **Joystick Test** - Connection verification with real-time axis and button display
- **Interactive Menu** - Organized navigation with sections for games, tools, demos, and utilities

### GPU-Accelerated Rendering

The project includes a full GPU rendering pipeline for high-performance visualization:

- **Interactive Shader Controller** - Real-time parameter tweaking with joystick
- **GIF Preview** - Quick animated previews for sharing
- **Video Export** - YouTube Shorts, TikTok, Instagram formats
- **Storyboard System** - Keyframe-based animation planning with contact sheets

See the [GPU Visualizer CLI Guide](docs/guides/gpu-visualizer-guide.md) for usage examples.

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

See [Joystick Controls](docs/joystick-controls.md) for detailed controller mappings and troubleshooting.

## Tech Stack

- **Python 3.8+**
- **pygame** - Joystick input handling and window management
- **blessed** - Terminal rendering and control
- **moderngl** - OpenGL 3.3+ GPU rendering
- **Pillow** - Image processing and GIF export
- **imageio** / **imageio-ffmpeg** - Video encoding

## Project Structure

```
atari_style/
├── core/
│   ├── renderer.py        # Terminal rendering engine (double-buffered)
│   ├── input_handler.py   # Unified keyboard/joystick input
│   ├── menu.py            # Interactive menu system
│   └── gl/                # GPU rendering pipeline
│       ├── gl_renderer.py       # OpenGL context management
│       ├── shader_controller.py # Interactive shader control
│       ├── video_export.py      # MP4/format export
│       ├── gif_preview.py       # Animated GIF generation
│       ├── storyboard.py        # Keyframe animation system
│       └── composite_manager.py # Multi-effect composites
├── shaders/               # GLSL shaders
│   ├── effects/           # Effect shaders (plasma, mandelbrot, tunnel)
│   └── post/              # Post-processing (CRT, scanlines)
├── demos/
│   ├── games/             # Arcade games
│   ├── visualizers/       # Visual demos
│   └── tools/             # Utilities
├── storyboards/           # Animation storyboard definitions
└── main.py                # Entry point with menu

docs/
├── getting-started/       # New user onboarding
├── guides/                # How-to guides (GPU visualizer, etc.)
├── reference/             # Quick reference documentation
├── architecture/          # System design docs
└── archive/               # Historical development notes
```

## Development

### Running Individual Demos

```bash
# Games
python -c "from atari_style.demos.games.pacman import run_pacman; run_pacman()"
python -c "from atari_style.demos.games.galaga import run_galaga; run_galaga()"
python -c "from atari_style.demos.games.grandprix import run_grandprix; run_grandprix()"
python -c "from atari_style.demos.games.breakout import run_breakout; run_breakout()"

# Tools
python -c "from atari_style.demos.tools.ascii_painter import run_ascii_painter; run_ascii_painter()"

# Demos
python -c "from atari_style.demos.visualizers.starfield import run_starfield; run_starfield()"
python -c "from atari_style.demos.visualizers.screensaver import run_screensaver; run_screensaver()"
python -c "from atari_style.demos.visualizers.platonic_solids import run_platonic_solids; run_platonic_solids()"
```

## Roadmap

### Vision 2025

atari-style is evolving along four strategic pillars:

1. **Foundation & Philosophy** - Defining what "atari-style" means as an aesthetic
2. **Architecture & Extensibility** - Unix composability and plugin architecture
3. **AI-Native Development** - Human-AI collaboration patterns for creative tools
4. **Ecosystem & Community** - Integration with jcaldwell-labs projects and community contributions

See [Issue #75](https://github.com/jcaldwell-labs/atari-style/issues/75) for the full strategic roadmap.

### GPU-Accelerated Visualizers (Complete)

All core GPU features are now implemented:

- **Shader Effects** - Plasma, Mandelbrot, Tunnel running on GPU at 60+ FPS
- **Video Export** - YouTube Shorts, TikTok, Instagram format presets
- **Storyboard System** - Keyframe-based animation planning
- **Composite Animations** - Multi-effect fusion (Plasma→Lissajous, Flux→Spiral)

### In Progress

- **Video Production Pipeline** - Educational video series (#28-31)
- **Flux Control Game** - Interactive game built on flux patterns (#21-24)
- **Documentation** - Comprehensive guides and tutorials (#76)

See [docs/shader-roadmap.md](docs/shader-roadmap.md) for GPU implementation details.

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

## Testing

### Visual Regression Tests

Catch unintended visual changes with automated baseline comparison:

```bash
# Generate baseline images (commit these to repo)
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

# Compare current render against baselines
python -m atari_style.core.visual_test compare joystick_test

# Run all visual tests with pytest
pytest test_visual_regression.py -v
```

See [baselines/README.md](baselines/README.md) for complete documentation.

### Unit Tests

```bash
# Run all tests
python -m unittest discover -s . -p "test_*.py" -v

# Or with pytest
pytest --cov=. --cov-report=term
```

## Documentation

| Guide | Description |
|-------|-------------|
| [GPU Visualizer CLI](docs/guides/gpu-visualizer-guide.md) | Interactive shaders, GIF/video export, storyboards |
| [Visual Regression Tests](baselines/README.md) | Automated visual regression testing |
| [Joystick Controls](docs/joystick-controls.md) | Controller mappings and troubleshooting |
| [Getting Started](docs/getting-started/) | Installation and basic usage |
| [Architecture](docs/architecture.md) | System design overview |
| [Shader Roadmap](docs/shader-roadmap.md) | GPU implementation details |
| [All Documentation](docs/README.md) | Full documentation index |

## Related Projects

This project is part of the [jcaldwell-labs](https://github.com/jcaldwell-labs) ecosystem:

- **[boxes-live](https://github.com/jcaldwell-labs/boxes-live)** - Terminal canvas with joystick support (bidirectional integration via storyboard2canvas)

## License

MIT

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

**Built for retro terminal enthusiasts**
