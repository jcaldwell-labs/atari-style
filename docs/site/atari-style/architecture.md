---
title: "Architecture Overview"
weight: 2
---

# Architecture Overview

atari-style is built around three core modules that every demo uses, plus a registry that handles discovery and launching. Understanding these layers makes it easy to add new content.

## Module Relationships

```
atari_style/
├── core/
│   ├── renderer.py        # Terminal output, double buffering, colors
│   ├── input_handler.py   # Keyboard + joystick input abstraction
│   ├── menu.py            # Interactive menu with keyboard/joystick nav
│   ├── registry.py        # Content discovery, metadata, lazy loading
│   └── config.py          # Persistent settings (~/.atari-style/config.json)
├── utils/
│   └── fonts.py           # Cross-platform monospace font loading
├── demos/
│   ├── games/             # Pac-Man, Galaga, Grand Prix, Breakout, Claugger
│   ├── visualizers/       # Starfield, Screen Saver, Platonic Solids, Flux Control
│   └── tools/             # ASCII Painter, Canvas Explorer, Joystick Test
└── main.py                # Entry point — builds registry, constructs menu
```

All demos import from `..core`. No demo imports from another demo. The core modules have no knowledge of specific games.

## Renderer

`atari_style/core/renderer.py`

The `Renderer` class wraps the `blessed` library and provides double-buffered terminal output. Instead of writing directly to the terminal, all drawing calls write into an in-memory buffer. When `render()` is called, the buffer is flushed to the terminal in one pass, eliminating flicker.

**Double buffering**: The renderer maintains two parallel arrays — `buffer` (characters) and `color_buffer` (color names). Every frame starts with `clear_buffer()`, which resets both arrays to empty. Drawing calls like `set_pixel()` and `draw_text()` populate the arrays. `render()` then walks the arrays and emits terminal escape sequences.

**Color system**: Colors are passed as string names (`'red'`, `'bright_cyan'`, etc.) that map directly to `blessed`'s terminal color attributes. The `Color` class provides named constants (`Color.BRIGHT_CYAN`, `Color.RED`, etc.) to avoid magic strings. The `Palette` class groups colors into thematic sets (CLASSIC, PLASMA, MIDNIGHT, FOREST, FIRE, OCEAN, MONOCHROME).

**Aspect ratio**: Terminal characters are taller than they are wide (roughly 2:1). Demos that draw circles or other shapes that must look correct need to multiply Y coordinates by approximately 0.5 before rendering. This is a rendering guideline, not an automatic correction.

## InputHandler

`atari_style/core/input_handler.py`

`InputHandler` provides a unified interface for keyboard and joystick input. Demos call `get_input()` and receive an `InputType` enum value — they never deal with raw key codes or pygame events directly.

**Keyboard mapping**: Arrow keys and WASD map to directional `InputType` values. Enter and Space map to `SELECT`. Escape and Q map to `BACK`. X maps to `QUIT`.

**Joystick handling**: pygame is used exclusively for joystick input. The handler initializes on construction and attempts reconnection automatically if a joystick is unplugged and replugged (polling approximately every 30 frames). A 0.15 deadzone is applied to analog axes. Digital threshold for axis-to-direction conversion is 0.5.

**Health checks**: The handler performs periodic device health checks (every 1 second) to detect USB device issues before they cause system lockup. If the device becomes unresponsive, the handler marks it unhealthy and stops polling until reconnection succeeds.

**Analog state**: For demos that need raw analog values (paddle position, lateral drift), `get_joystick_state()` returns normalized `(x, y)` floats in the range -1.0 to 1.0 with deadzone already applied.

**Cleanup**: Always call `input_handler.cleanup()` in a `finally` block. This releases USB resources cleanly. Signal handlers (SIGINT, SIGTERM) are registered automatically and call emergency cleanup if the process is killed.

## ContentRegistry

`atari_style/core/registry.py`

The registry is the bridge between the main entry point and the demos. It stores `ContentMetadata` objects that describe each piece of content — its title, category, description, and how to launch it.

**Lazy resolution**: Demos are not imported at startup. Each `ContentMetadata` stores a dotted module path (`run_module`) and function name (`run_function_name`). The `run_function` property uses `importlib.import_module()` on first access and caches the result. This keeps startup fast regardless of how many demos are registered.

**Registration paths**:
1. `register_metadata()` — direct registration with a `ContentMetadata` instance
2. `register_callable()` — wraps an already-imported callable; no lazy import needed
3. `scan_directory()` — scans a directory for subdirectories containing `metadata.json` files

**Auto-discovery**: The `terminal_arcade/games/` directory (if present) is scanned automatically. Games in that directory that share IDs with hardcoded entries (pacman, galaga, etc.) overwrite the hardcoded entries, taking over launch responsibility.

**Categories**: `ContentCategory` has four values: `GAME`, `VISUALIZER`, `TOOL`, `SHADER_DEMO`. The menu displays categories in that order.

## Game Loop Pattern

Every demo follows the same five-method pattern:

```python
class MyDemo:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        # Initialize game state here

    def handle_input(self) -> bool:
        """Process input. Return False to exit."""
        inp = self.input_handler.get_input(timeout=0.016)
        if inp == InputType.BACK:
            return False
        # Handle other inputs
        return True

    def update(self, dt: float):
        """Advance game state by dt seconds."""
        pass

    def draw(self):
        """Draw current state to the renderer buffer."""
        self.renderer.clear_buffer()
        # All drawing calls go here
        self.renderer.render()

    def run(self):
        self.renderer.enter_fullscreen()
        try:
            while True:
                if not self.handle_input():
                    break
                self.update(dt)
                self.draw()
                time.sleep(0.033)  # ~30 FPS
        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_my_demo():
    MyDemo().run()
```

The entry function (`run_my_demo`) is the target registered in the `ContentRegistry`. `main.py` calls this function when the user selects the demo from the menu.

## Menu System

`atari_style/core/menu.py`

The `Menu` class renders a navigable list of `MenuItem` objects. Each `MenuItem` stores a display title, an action callable, and an optional description shown in a detail panel. Navigation uses `InputHandler` internally.

`main.py` builds the registry via `_build_registry()`, converts it to menu items via `_registry_to_menu_items()`, and passes the list to `Menu`. The menu runs until the user selects Exit or presses Q.

## Configuration

`atari_style/core/config.py`

The `Config` dataclass stores persistent settings in `~/.atari-style/config.json`. Currently it holds one field: `char_aspect` (default 0.5), which controls the assumed terminal character aspect ratio for shape calculations. Load with `Config.load()`, modify, then call `.save()`.
