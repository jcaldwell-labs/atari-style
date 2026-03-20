---
title: "Contributing"
weight: 5
---

# Contributing

This guide covers everything you need to contribute to atari-style — dev setup, running tests, code conventions, and how to add a new demo.

## Dev Setup

```bash
git clone https://github.com/jcaldwell-labs/atari-style.git
cd atari-style

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install in editable mode so changes take effect immediately
pip install -e .

# Install dev tools
pip install ruff
```

## Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests live in `tests/`. The naming convention is `test_<module>.py`. Run the full suite before submitting a PR.

**Coverage targets**: Core modules (`renderer`, `input_handler`, `registry`, `config`) require 80% line coverage. New demos need integration tests — not just "runs without error" checks, but assertions that verify observable outcomes.

## Linting

```bash
ruff check atari_style/ tests/
```

Fix all reported issues before opening a PR. The CI pipeline runs ruff and will block merges if it fails.

## Code Conventions

These conventions reduce review cycles by making the codebase predictable.

### Constants, Not Magic Numbers

Extract any number with meaning into a named constant at the top of the file:

```python
# Bad
if abs(axis_value) > 0.5:
    ...

# Good
DIGITAL_THRESHOLD = 0.5
if abs(axis_value) > DIGITAL_THRESHOLD:
    ...
```

### Type Hints on All Public Functions

Every function exposed outside its module must have complete type hints:

```python
# Bad
def run_bounce():
    BouncingBall().run()

# Good
def run_bounce() -> None:
    BouncingBall().run()
```

Private methods (prefixed with `_`) may omit hints if they are straightforward, but public methods and all `__init__` signatures must have them.

### Imports

Only import what you use. Remove unused imports before committing. Use relative imports within the package:

```python
# Within atari_style/demos/games/mygame.py
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType
```

Do not import demo modules from other demo modules.

### Docstrings

Public APIs require docstrings with Args and Returns sections:

```python
def get_input(self, timeout: float = 0.1) -> InputType:
    """Get input from keyboard or joystick.

    Args:
        timeout: Seconds to wait for keyboard input before checking joystick.

    Returns:
        InputType enum value, or InputType.NONE if no input within timeout.
    """
```

One-liner docstrings are fine for methods where the purpose is self-evident from the name and signature.

### Security

**HTML output**: Always escape user-supplied data before inserting into HTML strings:

```python
import html
safe_name = html.escape(user_filename)
```

**File paths**: Validate paths before opening files to prevent traversal attacks:

```python
requested = (base_dir / user_path).resolve()
if not str(requested).startswith(str(base_dir.resolve())):
    raise PermissionError("Path outside allowed directory")
```

**Large files**: Stream rather than loading into memory:

```python
CHUNK_SIZE = 8192
with open(path, 'rb') as f:
    while chunk := f.read(CHUNK_SIZE):
        output.write(chunk)
```

## Adding a New Demo

Follow these steps to add a new game, visualizer, or tool.

### 1. Choose a location

| Type | Directory |
|---|---|
| Game | `atari_style/demos/games/` |
| Visual demo | `atari_style/demos/visualizers/` |
| Tool | `atari_style/demos/tools/` |

### 2. Create your file

```bash
touch atari_style/demos/games/mygame.py
```

### 3. Implement the five-method pattern

```python
"""My game description."""

import time
from typing import Optional

from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


MY_CONSTANT = 42  # named constants, not magic numbers


class MyGame:
    """One-line description."""

    def __init__(self) -> None:
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        # initialize state

    def handle_input(self) -> bool:
        """Process input. Returns False to exit."""
        inp = self.input_handler.get_input(timeout=0.016)
        if inp == InputType.BACK:
            return False
        return True

    def update(self, dt: float) -> None:
        """Advance game state by dt seconds."""
        pass

    def draw(self) -> None:
        """Render the current frame."""
        self.renderer.clear_buffer()
        # drawing calls here
        self.renderer.render()

    def run(self) -> None:
        """Main game loop."""
        self.renderer.enter_fullscreen()
        last = time.time()
        try:
            while True:
                now = time.time()
                dt = min(now - last, 0.1)
                last = now
                if not self.handle_input():
                    break
                self.update(dt)
                self.draw()
        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_my_game() -> None:
    """Entry point for my game."""
    MyGame().run()
```

### 4. Register in main.py

Open `atari_style/main.py`. Find the appropriate registration block and add your entry:

```python
# For a game:
for game_id, title, desc, module, func in [
    # ... existing entries ...
    ("my-game", "My Game", "Short description of what it does",
     "atari_style.demos.games.mygame", "run_my_game"),
]:
```

For visualizers and tools, add to the corresponding block (`_viz` and `_tools` sections respectively).

### 5. Write a test

Create `tests/test_mygame.py`:

```python
"""Tests for my game."""

import unittest
from unittest.mock import patch, MagicMock


class TestMyGame(unittest.TestCase):

    @patch('atari_style.demos.games.mygame.Renderer')
    @patch('atari_style.demos.games.mygame.InputHandler')
    def test_initial_state(self, mock_input, mock_renderer):
        """Game initializes with expected default state."""
        mock_renderer.return_value.width = 80
        mock_renderer.return_value.height = 24

        from atari_style.demos.games.mygame import MyGame
        game = MyGame()

        # Assert concrete outcomes — not just "no exception"
        self.assertIsNotNone(game.renderer)
        self.assertIsNotNone(game.input_handler)

    @patch('atari_style.demos.games.mygame.Renderer')
    @patch('atari_style.demos.games.mygame.InputHandler')
    def test_handle_input_back_returns_false(self, mock_input, mock_renderer):
        """BACK input causes handle_input to return False."""
        from atari_style.core.input_handler import InputType
        mock_renderer.return_value.width = 80
        mock_renderer.return_value.height = 24
        mock_input.return_value.get_input.return_value = InputType.BACK

        from atari_style.demos.games.mygame import MyGame
        game = MyGame()
        result = game.handle_input()

        self.assertFalse(result)
```

### 6. Verify before submitting

Run through this checklist:

- [ ] Actually run the demo end-to-end and observe the behavior
- [ ] Test at different terminal sizes (small and large)
- [ ] Test with no joystick connected
- [ ] Confirm ESC exits cleanly without leaving the terminal in a bad state
- [ ] Run `ruff check atari_style/ tests/` — zero issues
- [ ] Run the full test suite — all tests pass
- [ ] Every test has at least one `assert` that checks a real outcome

## PR Process

1. Fork the repository and create a feature branch: `git checkout -b feat/my-game`
2. Make your changes following the conventions above
3. Run lint and tests
4. Push and open a PR against `master`
5. The PR description should explain what the demo does and include a screenshot or terminal recording if possible

PR titles follow conventional commits format:
- `feat: Add my game demo`
- `fix: Correct ball collision in bounce demo`
- `refactor: Extract shared physics utility`
- `docs: Update API reference for Renderer`

Keep PRs focused. A PR that adds a new demo should not also refactor unrelated core code — split those into separate PRs.
