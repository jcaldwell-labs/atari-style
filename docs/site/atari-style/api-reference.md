---
title: "API Reference"
weight: 3
---

# API Reference

This page documents all public APIs in the core modules. Import paths are absolute from the package root.

---

## Renderer

```python
from atari_style.core.renderer import Renderer, Color, Palette
```

### `Renderer`

Handles terminal rendering with double buffering. All drawing operations write to an in-memory buffer; call `render()` to flush to the terminal.

#### Constructor

```python
renderer = Renderer()
```

Initializes the terminal connection and creates empty character and color buffers sized to the current terminal dimensions.

**Attributes after construction**:
- `renderer.width: int` — terminal width in columns
- `renderer.height: int` — terminal height in rows
- `renderer.term` — the underlying `blessed.Terminal` instance

---

#### `clear_buffer() -> None`

Reset all characters and colors in the buffer to empty. Call at the start of each frame before drawing.

```python
renderer.clear_buffer()
```

---

#### `set_pixel(x: int, y: int, char: str = '█', color: Optional[str] = None) -> None`

Write a single character at column `x`, row `y`. Out-of-bounds coordinates are silently ignored.

```python
renderer.set_pixel(10, 5, '@', Color.BRIGHT_GREEN)
renderer.set_pixel(0, 0, '.')          # no color — uses terminal default
```

**Parameters**:
- `x` — column (0-indexed, left to right)
- `y` — row (0-indexed, top to bottom)
- `char` — character to draw; only the first character of the string is used
- `color` — color name string, or `None` for terminal default

---

#### `draw_text(x: int, y: int, text: str, color: Optional[str] = None) -> None`

Draw a string of characters starting at `(x, y)`. Characters that fall outside the buffer bounds are silently ignored.

```python
renderer.draw_text(2, 1, "SCORE: 1000", Color.YELLOW)
```

**Parameters**:
- `x` — starting column
- `y` — row
- `text` — string to render
- `color` — color name string, or `None`

---

#### `draw_box(x: int, y: int, width: int, height: int, char: str = '█', color: Optional[str] = None) -> None`

Fill a rectangular region with `char`.

```python
renderer.draw_box(5, 5, 10, 3, '░', Color.BLUE)
```

**Parameters**:
- `x`, `y` — top-left corner
- `width`, `height` — dimensions in characters
- `char` — fill character
- `color` — color name string, or `None`

---

#### `draw_border(x: int, y: int, width: int, height: int, color: Optional[str] = None) -> None`

Draw a hollow rectangle using box-drawing characters. Uses `─`, `│`, `┌`, `┐`, `└`, `┘`.

```python
renderer.draw_border(0, 0, renderer.width, renderer.height, Color.CYAN)
```

**Parameters**:
- `x`, `y` — top-left corner
- `width`, `height` — outer dimensions
- `color` — color name string, or `None`

---

#### `render() -> None`

Flush the current buffer to the terminal. Walks the buffer arrays and emits terminal cursor positioning and color escape sequences. Call once per frame after all drawing is complete.

```python
renderer.render()
```

---

#### `enter_fullscreen() -> None`

Switch the terminal to fullscreen (alternate screen) mode and hide the cursor. Call before the game loop starts.

```python
renderer.enter_fullscreen()
```

---

#### `exit_fullscreen() -> None`

Restore the terminal to normal mode and show the cursor. Always call in a `finally` block to ensure the terminal is not left in fullscreen state if the program crashes.

```python
try:
    renderer.enter_fullscreen()
    # game loop
finally:
    renderer.exit_fullscreen()
```

---

#### `clear_screen() -> None`

Clear the terminal display and move the cursor to the home position. Distinct from `clear_buffer()` — this writes directly to the terminal rather than the buffer.

```python
renderer.clear_screen()
```

---

#### `save_screenshot(path: str) -> bool`

Export the current buffer as a PNG image. Requires `Pillow` to be installed.

Renders each buffered character using a monospace font into an RGB image with a dark background (Dracula theme: `#1e1e2e`). Falls back to PIL's default bitmap font if no TrueType monospace fonts are found on the system.

```python
success = renderer.save_screenshot("/tmp/screenshot.png")
if not success:
    print("Pillow not installed")
```

**Parameters**:
- `path` — output file path; parent directory is created if it does not exist

**Returns**: `True` if the PNG was written successfully, `False` if Pillow is not installed.

**Color support**: Named colors from `Color` constants are mapped to RGB values in the output image.

---

### `Color`

String constants for terminal colors. Pass these to any `color` parameter.

**Standard colors**:

| Constant | Value | Constant | Value |
|---|---|---|---|
| `Color.BLACK` | `'black'` | `Color.RED` | `'red'` |
| `Color.GREEN` | `'green'` | `Color.BLUE` | `'blue'` |
| `Color.YELLOW` | `'yellow'` | `Color.MAGENTA` | `'magenta'` |
| `Color.CYAN` | `'cyan'` | `Color.WHITE` | `'white'` |

**Bright colors**:

| Constant | Value | Constant | Value |
|---|---|---|---|
| `Color.BRIGHT_BLACK` | `'bright_black'` | `Color.BRIGHT_RED` | `'bright_red'` |
| `Color.BRIGHT_GREEN` | `'bright_green'` | `Color.BRIGHT_BLUE` | `'bright_blue'` |
| `Color.BRIGHT_YELLOW` | `'bright_yellow'` | `Color.BRIGHT_MAGENTA` | `'bright_magenta'` |
| `Color.BRIGHT_CYAN` | `'bright_cyan'` | `Color.BRIGHT_WHITE` | `'bright_white'` |

**Alias**:
- `Color.GRAY` = `'bright_black'`

---

### `Palette`

Predefined color lists for thematic rendering.

```python
from atari_style.core.renderer import Palette

colors = Palette.CLASSIC      # list of color strings
colors = Palette.get('fire')  # by name
```

**Available palettes**:

| Name | Colors |
|---|---|
| `CLASSIC` | bright_cyan, bright_green, bright_yellow, bright_red, bright_magenta, white |
| `PLASMA` | blue, cyan, green, yellow, red, magenta |
| `MIDNIGHT` | blue, magenta, bright_magenta, cyan, bright_cyan, white |
| `FOREST` | green, bright_green, yellow, cyan, bright_white |
| `FIRE` | red, bright_red, yellow, bright_yellow, white |
| `OCEAN` | blue, cyan, bright_cyan, green, bright_blue, white |
| `MONOCHROME` | green, bright_green, bright_white |

#### `Palette.get(name: str) -> list`

Return a palette by name (case-insensitive). Falls back to `CLASSIC` if the name is not recognized.

```python
colors = Palette.get('midnight')
```

---

## InputHandler

```python
from atari_style.core.input_handler import InputHandler, InputType
```

### `InputType`

Enum of possible input events returned by `get_input()`.

| Member | Value | Triggered by |
|---|---|---|
| `InputType.NONE` | 0 | No input within timeout |
| `InputType.UP` | 1 | Up arrow, W key, joystick axis up |
| `InputType.DOWN` | 2 | Down arrow, S key, joystick axis down |
| `InputType.LEFT` | 3 | Left arrow, A key, joystick axis left |
| `InputType.RIGHT` | 4 | Right arrow, D key, joystick axis right |
| `InputType.SELECT` | 5 | Enter, Space, joystick button 0 |
| `InputType.BACK` | 6 | Escape, Q key, joystick button 1 |
| `InputType.QUIT` | 7 | X key |

### `InputHandler`

```python
handler = InputHandler()
```

On construction, initializes pygame, attempts joystick detection, and registers signal handlers for clean shutdown.

---

#### `get_input(timeout: float = 0.1) -> InputType`

Block for up to `timeout` seconds waiting for keyboard input, then check joystick state. Returns the first recognized event, or `InputType.NONE` if nothing was pressed.

```python
inp = handler.get_input(timeout=0.016)  # ~60 FPS budget
if inp == InputType.BACK:
    return False
```

**Parameters**:
- `timeout` — seconds to wait for keyboard input; shorter = more responsive but higher CPU usage

**Notes**:
- Keyboard takes priority over joystick
- Joystick buttons use edge detection (fires once on press, not while held)
- Automatically attempts joystick reconnection if disconnected

---

#### `get_joystick_state() -> Tuple[float, float]`

Return the current joystick axis state as `(x, y)`, each normalized to -1.0 to 1.0. A 0.15 deadzone is applied. Returns `(0.0, 0.0)` if no joystick is connected or if a device health check fails.

```python
x, y = handler.get_joystick_state()
paddle_x += x * speed * dt
```

---

#### `get_joystick_buttons() -> dict`

Return a dictionary mapping button index to boolean state for all buttons on the connected joystick. Returns an empty dict if no joystick is connected.

```python
buttons = handler.get_joystick_buttons()
if buttons.get(0):   # button 0 held
    fire()
```

---

#### `verify_joystick() -> dict`

Return a dictionary describing the connected joystick. Useful for the Joystick Test utility.

```python
info = handler.verify_joystick()
# {'connected': True, 'name': 'Xbox Controller', 'axes': 6, 'buttons': 17}
# {'connected': False, 'name': None, 'axes': 0, 'buttons': 0}
```

**Returns**:
- `connected: bool` — whether a joystick is initialized
- `name: Optional[str]` — joystick name reported by pygame
- `axes: int` — number of analog axes
- `buttons: int` — number of buttons

---

#### `cleanup() -> None`

Release joystick resources and remove this instance from the signal handler registry. Always call in a `finally` block.

```python
try:
    handler = InputHandler()
    # game loop
finally:
    handler.cleanup()
```

---

## ContentRegistry

```python
from atari_style.core.registry import ContentRegistry, ContentMetadata, ContentCategory
```

### `ContentCategory`

Enum for organizing content in the menu.

| Member | Value |
|---|---|
| `ContentCategory.GAME` | `'game'` |
| `ContentCategory.VISUALIZER` | `'visualizer'` |
| `ContentCategory.TOOL` | `'tool'` |
| `ContentCategory.SHADER_DEMO` | `'shader_demo'` |

### `ContentMetadata`

Dataclass describing a piece of registered content.

**Required fields**:
- `id: str` — unique identifier (kebab-case slug)
- `title: str` — human-readable display name
- `category: ContentCategory`
- `description: str` — short description for menu display

**Launch spec** (at least one required to be launchable):
- `run_module: Optional[str]` — dotted module path (e.g. `'atari_style.demos.games.pacman'`)
- `run_function_name: Optional[str]` — function name within the module (e.g. `'run_pacman'`)

**Optional fields**:
- `backend: RenderingBackend` — default `TERMINAL`
- `joystick_support: bool` — default `True`
- `keyboard_support: bool` — default `True`
- `controls_hint: str` — short controls string
- `has_intro: bool` — whether content has an intro sequence
- `is_new: bool` — flag for highlighting in menus
- `tags: List[str]` — searchable tags
- `version: str` — default `'1.0'`
- `author: str`
- `source_path: Optional[Path]` — filesystem path to source directory

**Property**:

`run_function: Optional[Callable]` — lazily imports and returns the run callable on first access; caches the result. Returns `None` if the module cannot be imported.

### `ContentRegistry`

```python
registry = ContentRegistry(expected_minimum=18)
```

**Parameters**:
- `expected_minimum: int` — if > 0, logs a warning when content count drops below this threshold after scan operations

---

#### `register_metadata(metadata: ContentMetadata) -> None`

Register a `ContentMetadata` instance. Overwrites existing entries with the same `id`.

---

#### `register_callable(id, title, category, description, run_fn, **kwargs) -> ContentMetadata`

Register a directly imported callable. Stores the callable immediately without lazy import.

```python
from atari_style.demos.games.pacman import run_pacman
registry.register_callable(
    id="pacman",
    title="Pac-Man",
    category=ContentCategory.GAME,
    description="Classic maze chase game",
    run_fn=run_pacman,
)
```

---

#### `scan_directory(directory: Path, default_category: ContentCategory = ContentCategory.GAME) -> int`

Scan a directory for subdirectories containing `metadata.json` files. Each valid file is parsed and registered. Returns the number of items registered from this scan.

---

#### `get(id: str) -> Optional[ContentMetadata]`

Look up a single content item by its `id`.

---

#### `get_by_category(category: ContentCategory) -> List[ContentMetadata]`

Return all content items in a given category.

---

#### `get_all() -> List[ContentMetadata]`

Return all registered content.

---

#### `search(query: str) -> List[ContentMetadata]`

Case-insensitive substring search across title, description, and tags.

---

#### `count() -> int`

Total number of registered items.

---

#### `category_counts() -> Dict[ContentCategory, int]`

Count of items per category.

---

## Config

```python
from atari_style.core.config import Config
```

### `Config`

Dataclass for persistent application settings. Stored at `~/.atari-style/config.json`.

**Fields**:
- `char_aspect: float` — terminal character aspect ratio (width/height). Default `0.5`. Valid range: 0.2 to 1.0.

#### `Config.load() -> Config`

Load config from file, or return defaults if the file does not exist or is malformed.

```python
config = Config.load()
print(config.char_aspect)  # 0.5
```

#### `config.save() -> None`

Write current config to `~/.atari-style/config.json`. Creates the directory if needed.

```python
config = Config.load()
config.char_aspect = 0.55
config.save()
```

---

## load_monospace_font

```python
from atari_style.utils.fonts import load_monospace_font
```

#### `load_monospace_font(size: int, preferred_paths: Optional[list[str]] = None) -> ImageFont.FreeTypeFont`

Load a monospace TrueType font for use with Pillow. Tries `preferred_paths` first, then a built-in list of common system font paths for Linux, macOS, and Windows. Falls back to PIL's default bitmap font if nothing is found.

```python
font = load_monospace_font(16)
font = load_monospace_font(22, preferred_paths=['/my/custom/mono.ttf'])
```

**Default search paths** (in order):
1. `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`
2. `/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf`
3. `/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf`
4. `/usr/share/fonts/TTF/DejaVuSansMono.ttf`
5. `/System/Library/Fonts/Menlo.ttc`
6. `C:/Windows/Fonts/consola.ttf`

**Parameters**:
- `size` — font size in points
- `preferred_paths` — optional list of paths to try before the defaults

**Returns**: A `PIL.ImageFont.FreeTypeFont` instance (or the built-in bitmap font as fallback).
