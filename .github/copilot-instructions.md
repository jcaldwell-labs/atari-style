# GitHub Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Project Overview

Atari-style is a comprehensive collection of terminal-based interactive games, creative tools, and visual demos inspired by classic Atari aesthetics. Features playable arcade experiences using ASCII/ANSI terminal graphics with full joystick and keyboard support.

**Status**: Active development
**Language**: Python 3.8+
**Dependencies**: pygame (joystick), blessed (terminal rendering)

Key features:
- 4 classic arcade games: Pac-Man, Galaga, Grand Prix, Breakout
- ASCII art painting tool with 6 drawing tools
- Visual demos: Starfield, Screen Saver, Platonic Solids
- Full joystick support with keyboard fallback
- Double-buffered rendering for smooth 30-60 FPS animation

## Build System

```bash
# Setup virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .

# Run the application
python run.py
# or
python -m atari_style.main
# or (after pip install)
atari-style

# Run tests
python -m unittest discover -s . -p "test_*.py" -v
# or with pytest
pytest --cov=. --cov-report=term
```

**Dependencies:**
- `pygame>=2.5.0` - Joystick input handling
- `blessed>=1.20.0` - Terminal rendering and control

## Architecture

### Directory Structure

```
atari-style/
├── atari_style/               # Main package
│   ├── __init__.py
│   ├── main.py                # Entry point with interactive menu
│   ├── core/                  # Core framework modules
│   │   ├── __init__.py
│   │   ├── renderer.py        # Terminal rendering engine
│   │   ├── input_handler.py   # Unified keyboard/joystick input
│   │   └── menu.py            # Interactive menu system
│   └── demos/                 # Game and demo implementations
│       ├── pacman.py          # Pac-Man maze chase
│       ├── galaga.py          # Space shooter
│       ├── grandprix.py       # 3D racing
│       ├── breakout.py        # Paddle and ball
│       ├── ascii_painter.py   # Drawing tool
│       ├── starfield.py       # 3D space flight
│       ├── screensaver.py     # 8 parametric animations
│       ├── platonic_solids.py # 3D geometry viewer
│       └── joystick_test.py   # Joystick verification
├── terminal_arcade/           # Alternative implementation (12-game version)
├── requirements.txt
├── setup.py                   # Package configuration
├── run.py                     # Main entry script
├── test_*.py                  # Test files
└── .github/
    └── workflows/python.yml   # CI/CD pipeline
```

### Core Components

**Renderer** (`core/renderer.py`):
- `Renderer` class: Double-buffered terminal rendering
- Color constants: RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, WHITE, BRIGHT_*
- Methods: `set_pixel()`, `draw_text()`, `draw_box()`, `draw_border()`, `render()`
- Fullscreen management: `enter_fullscreen()`, `exit_fullscreen()`

**InputHandler** (`core/input_handler.py`):
- Unified keyboard and joystick input
- Auto-joystick detection
- Deadzone handling for analog sticks
- Input types: UP, DOWN, LEFT, RIGHT, SELECT, BACK, QUIT
- Methods: `get_input()`, `get_joystick_state()`, `verify_joystick()`

**Menu** (`core/menu.py`):
- `Menu` and `MenuItem` classes
- Keyboard and joystick navigation
- Decorative borders and highlighting

## Code Style and Conventions

- **Python conventions**: PEP 8 style guidelines
- **Module organization**: Core framework in `core/`, games in `demos/`
- **Entry functions**: Each demo has `run_<demo_name>()` function
- **Game loop pattern**: init -> draw -> update -> handle_input

**Color System**:
- Use predefined `Color` constants
- Colors are optional in render methods (default to white)

**Terminal Aspect Ratio**:
- Characters are not square
- Multiply Y coordinates by ~0.5 for circles/aspect correction

**Performance**:
- Target ~30 FPS with `time.sleep(0.033)`
- Use double buffering (always `clear_buffer()` before drawing)
- Limit pixel density for complex animations

## Before Committing (Required Steps)

Run these commands before every commit:

1. **Lint**: `ruff check .` or `flake8` - Check for issues
2. **Test**: `python -m unittest discover -s . -p "test_*.py" -v`
3. **Manual test**: `python run.py` - Verify basic functionality

```bash
# Quick pre-commit check
ruff check . && python -m unittest discover -s . -p "test_*.py" -v
```

## Common Development Tasks

### Adding a New Demo
1. Create new file in `atari_style/demos/`
2. Import core modules:
   ```python
   from ..core.renderer import Renderer, Color
   from ..core.input_handler import InputHandler, InputType
   ```
3. Create demo class with methods:
   - `__init__()` - Setup renderer, input handler
   - `draw()` - Render frame to buffer
   - `update()` - Update game state
   - `handle_input()` - Process user input
   - `run()` - Main loop
4. Create entry function: `def run_your_demo():`
5. Add to menu in `atari_style/main.py`:
   ```python
   from .demos.your_demo import run_your_demo
   menu_items.append(MenuItem("Your Demo", run_your_demo, "Description"))
   ```

### Game Loop Pattern
```python
def run(self):
    try:
        self.renderer.enter_fullscreen()
        while self.running:
            self.handle_input()
            self.update()
            self.renderer.clear_buffer()
            self.draw()
            self.renderer.render()
            time.sleep(0.033)  # ~30 FPS
    finally:
        self.renderer.exit_fullscreen()
```

### Input Controls
All demos support:
- **Arrow Keys** or **WASD**: Navigation/Movement
- **Enter** or **Space**: Select/Action
- **ESC** or **Q**: Back/Exit
- **Joystick**: Full analog and button support

## Pull Request Standards

When creating PRs, follow these rules:

1. **Always link the issue**: Use `Fixes #N` or `Closes #N`
2. **Fill in all sections**: Never leave placeholder text

**Required PR format:**
```markdown
## Summary
[2-3 sentences describing what and why]

Fixes #[issue-number]

## Changes
- [Actual change 1]
- [Actual change 2]

## Testing
- [x] All tests pass
- [x] Manual gameplay tested
- [x] Joystick and keyboard tested

## Type
- [x] New feature | Bug fix | Refactor | Docs | CI
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/python.yml`):
- Triggers: Push to main/master, pull requests
- Python versions: 3.8, 3.9, 3.10, 3.11
- Steps: Install deps, ruff lint, flake8 lint, run tests

## Game Highlights

**Pac-Man** (~30 FPS):
- 4 ghost AI personalities (Blinky, Pinky, Inky, Clyde)
- BFS pathfinding, mode switching (Chase/Scatter/Frightened)
- Power-up scoring: 200->400->800->1600 points

**Galaga** (~60 FPS):
- 3 enemy types with wave formations
- Dive attacks, UFO bonus ships
- Accuracy tracking

**Grand Prix** (~30 FPS):
- Real-time 3D road with perspective
- 300-segment track with curves/hills
- 8 AI opponents

**Breakout** (~60 FPS):
- 5 power-up types
- 3 brick types (normal/strong/unbreakable)
- Combo system

**ASCII Painter** (~30 FPS):
- 6 tools, 4 palettes, 14 colors
- Undo/redo (20 levels)
- Export to .txt and .ansi

## Additional Documentation

- **README.md** - Project overview and features
- Test files document functionality via test cases
