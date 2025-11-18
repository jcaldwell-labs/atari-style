

# Atari-Style Terminal Demos

A collection of terminal-based interactive demos and games inspired by classic Atari aesthetics, featuring joystick support and ASCII/ANSI graphics.

## Features

### Implemented

- **Menu System** - Interactive menu for demo selection with keyboard and joystick support
- **Joystick Connection Verification** - Visual test utility showing real-time joystick state
- **Starfield Demo** - 3D space flight simulation with joystick-controlled speed and multiple color modes
- **Screen Saver** - Eight parametric animations (Lissajous, Spirals, Wave Circles, Plasma, Mandelbrot Zoomer, Fluid Lattice, Particle Swarm, Tunnel Vision) with real-time joystick control over animation parameters. 8-directional joystick input adjusts 4 parameters per animation using **opposite direction pairs** (UP↔DOWN, LEFT↔RIGHT, and 2 diagonal pairs). Runs at 60 FPS.

### Roadmap (Future Features)

- Pac-Man style maze game with character movement and obstacles
- Platonic solid animations (see platonic explorer)
- ASCII art editor with joystick control
- First-person POV car racing game

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
```

### Controls

- **Arrow Keys** or **WASD** - Navigate menus and control demos
- **Enter** or **Space** - Select menu items
- **ESC** or **Q** - Back/Exit
- **Joystick** - Full analog stick and button support

## Tech Stack

- **Python 3.8+**
- **pygame** - Joystick input handling
- **blessed** - Terminal rendering and control

## Project Structure

```
atari_style/
├── core/
│   ├── renderer.py      # Terminal rendering engine
│   ├── input_handler.py # Keyboard/joystick input
│   └── menu.py          # Menu system
├── demos/
│   ├── starfield.py     # Starfield demo
│   ├── screensaver.py   # Parametric animations
│   └── joystick_test.py # Joystick verification
└── main.py              # Entry point
```

## Related Projects

Similar to terminal-stars but expanded with a menu system and multiple playable demos.

## License

MIT

