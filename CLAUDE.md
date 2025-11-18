# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**atari-style** is a collection of terminal-based interactive demos and games inspired by classic Atari aesthetics. The project aims to create playable experiences using ASCII/ANSI terminal graphics with joystick support.

### Planned Features (from README.md)

The project roadmap includes:
- Menu system for demo selection
- Joystick connection verification
- Starfield demo with joystick-controlled animation parameters
- Pac-Man style maze game with character movement and obstacles
- Screen saver with parametric animations
- Platonic solid animations (reference: platonic explorer)
- ASCII art editor with joystick control
- First-person POV car racing game

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

### Demo Modules (`atari_style/demos/`)

Each demo is self-contained with a `run_*()` function:

- **`starfield.py`**: 3D starfield simulation
  - 3D-to-2D projection for star positions
  - Joystick-controlled speed (warp drive effect)
  - Multiple color modes: monochrome, rainbow, speed-based
  - Motion trails at high speed
  - ~30 FPS animation loop

- **`screensaver.py`**: Parametric animation collection with joystick control
  - Eight animation modes with 4 adjustable parameters each:
    1. Lissajous curves (frequency X/Y, phase, resolution)
    2. Spirals (count, speed, tightness, scale)
    3. Concentric wave circles (count, amplitude, frequency, spacing)
    4. Plasma effect (X/Y/diagonal/radial frequencies)
    5. Mandelbrot zoomer (zoom, center X/Y, detail)
    6. Fluid lattice (rain rate, wave speed, drop power, damping)
    7. Particle swarm (count, speed, cohesion, separation)
    8. Tunnel vision (depth speed, rotation, size, color speed)
  - **Help System**: Press 'H' for parameter descriptions modal
  - **Save Slots**: Buttons 2-5 for parameter presets (hold=save, tap=load)
  - 8-directional joystick control using opposite pairs
  - Real-time parameter display and adjustment
  - 60 FPS rendering with 2x animation speed multiplier
  - Physics simulations: fluid dynamics, boid flocking
  - Fractal rendering: Mandelbrot set with auto-zoom
  - Classic demo-scene effects: tunnel vision

- **`joystick_test.py`**: Joystick verification utility
  - Visual crosshair showing analog stick position
  - Real-time button state display
  - Axis value readouts
  - Connection status and device info

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
# Starfield
python -c "from atari_style.demos.starfield import run_starfield; run_starfield()"

# Screen saver
python -c "from atari_style.demos.screensaver import run_screensaver; run_screensaver()"

# Joystick test
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
