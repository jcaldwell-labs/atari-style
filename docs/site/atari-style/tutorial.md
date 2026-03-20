---
title: "Building Your First Game"
weight: 4
---

# Building Your First Game

This tutorial walks through building a complete bouncing ball demo from scratch. By the end you will have a working game that renders to the terminal, responds to keyboard and joystick input, and appears in the main menu.

The complete source is at the bottom of this page. Each section builds on the last.

## What We're Building

A ball bounces around the terminal. Arrow keys or a joystick change its direction. ESC exits. Simple — but it touches every part of the engine.

## Step 1: Create the File

Create `atari_style/demos/games/bounce.py`.

```python
"""Bouncing ball demo."""

import time
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType
```

The relative imports (`...core`) work because this file lives three package levels deep. If you put your demo elsewhere, adjust the number of dots.

## Step 2: The Skeleton Class

Every demo follows the same five-method pattern: `__init__`, `handle_input`, `update`, `draw`, `run`.

```python
class BouncingBall:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Ball position (floats for smooth movement)
        self.x = self.renderer.width / 2
        self.y = self.renderer.height / 2

        # Ball velocity in characters per second
        self.vx = 20.0
        self.vy = 10.0

        self.running = True

    def handle_input(self) -> bool:
        """Return False to exit."""
        inp = self.input_handler.get_input(timeout=0.016)

        if inp == InputType.BACK:
            return False
        elif inp == InputType.UP:
            self.vy = -abs(self.vy)
        elif inp == InputType.DOWN:
            self.vy = abs(self.vy)
        elif inp == InputType.LEFT:
            self.vx = -abs(self.vx)
        elif inp == InputType.RIGHT:
            self.vx = abs(self.vx)

        return True

    def update(self, dt: float):
        """Advance physics by dt seconds."""
        pass  # we'll add this in step 4

    def draw(self):
        """Render the current frame."""
        pass  # we'll add this in step 3

    def run(self):
        self.renderer.enter_fullscreen()
        last_time = time.time()
        try:
            while self.running:
                now = time.time()
                dt = now - last_time
                last_time = now

                if not self.handle_input():
                    break
                self.update(dt)
                self.draw()
        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_bounce():
    BouncingBall().run()
```

At this point the demo runs (try it: `python -c "from atari_style.demos.games.bounce import run_bounce; run_bounce()"`), but the screen is blank.

## Step 3: Add Rendering

Replace the `draw` method:

```python
def draw(self):
    self.renderer.clear_buffer()

    # Border so we can see the walls
    self.renderer.draw_border(
        0, 0,
        self.renderer.width, self.renderer.height,
        Color.CYAN
    )

    # Ball
    bx = int(self.x)
    by = int(self.y)
    self.renderer.set_pixel(bx, by, 'O', Color.BRIGHT_YELLOW)

    # HUD
    self.renderer.draw_text(
        2, 1,
        f"Pos: ({bx}, {by})  Vel: ({self.vx:.0f}, {self.vy:.0f})",
        Color.WHITE
    )
    self.renderer.draw_text(2, 2, "Arrows: change direction  ESC: exit", Color.GRAY)

    self.renderer.render()
```

Three things happen every frame:
1. `clear_buffer()` resets the buffer to empty
2. Drawing calls (`draw_border`, `set_pixel`, `draw_text`) populate the buffer
3. `render()` flushes the buffer to the terminal

The ball is at `int(self.x), int(self.y)` because the renderer works in integer character coordinates, while physics uses floats.

## Step 4: Add Physics

Replace the `update` method:

```python
def update(self, dt: float):
    # Move
    self.x += self.vx * dt
    self.y += self.vy * dt

    # Bounce off left/right walls (leave 1-char margin for border)
    if self.x < 1:
        self.x = 1
        self.vx = abs(self.vx)
    elif self.x >= self.renderer.width - 1:
        self.x = self.renderer.width - 2
        self.vx = -abs(self.vx)

    # Bounce off top/bottom walls
    if self.y < 1:
        self.y = 1
        self.vy = abs(self.vy)
    elif self.y >= self.renderer.height - 1:
        self.y = self.renderer.height - 2
        self.vy = -abs(self.vy)
```

Note the terminal aspect ratio: characters are taller than they are wide (approximately 2:1). The ball's X velocity (`20.0`) is higher than Y (`10.0`) to compensate, so it moves at roughly the same apparent speed in both directions.

Run it again and you should see the ball bouncing around inside the border.

## Step 5: Add to the Menu

Open `atari_style/main.py` and find the games registration block. Add your demo:

```python
for game_id, title, desc, module, func in [
    ("pacman", "Pac-Man", "Classic maze chase game with ghost AI",
     "atari_style.demos.games.pacman", "run_pacman"),
    # ... existing games ...
    ("bounce", "Bouncing Ball",
     "A ball bounces around. Arrows change direction.",
     "atari_style.demos.games.bounce", "run_bounce"),  # add this
]:
```

The registry uses lazy resolution — your module is not imported until the user actually selects the demo from the menu.

Launch `python run.py` and your demo will appear in the Games section.

## Complete Source

```python
"""Bouncing ball demo.

A ball bounces around the terminal. Arrow keys or joystick change
its direction. ESC exits.
"""

import time
from typing import Tuple

from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


class BouncingBall:
    """Bouncing ball demo."""

    def __init__(self) -> None:
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Ball position (floats for smooth movement)
        self.x: float = self.renderer.width / 2.0
        self.y: float = self.renderer.height / 2.0

        # Velocity: characters per second
        # X is higher than Y to compensate for terminal aspect ratio
        self.vx: float = 20.0
        self.vy: float = 10.0

    def handle_input(self) -> bool:
        """Process input. Returns False when the demo should exit."""
        inp = self.input_handler.get_input(timeout=0.016)

        if inp == InputType.BACK:
            return False
        elif inp == InputType.UP:
            self.vy = -abs(self.vy)
        elif inp == InputType.DOWN:
            self.vy = abs(self.vy)
        elif inp == InputType.LEFT:
            self.vx = -abs(self.vx)
        elif inp == InputType.RIGHT:
            self.vx = abs(self.vx)

        return True

    def update(self, dt: float) -> None:
        """Advance physics by dt seconds.

        Args:
            dt: Time since last frame in seconds.
        """
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce off walls (1-char margin for border)
        if self.x < 1:
            self.x = 1.0
            self.vx = abs(self.vx)
        elif self.x >= self.renderer.width - 1:
            self.x = float(self.renderer.width - 2)
            self.vx = -abs(self.vx)

        if self.y < 1:
            self.y = 1.0
            self.vy = abs(self.vy)
        elif self.y >= self.renderer.height - 1:
            self.y = float(self.renderer.height - 2)
            self.vy = -abs(self.vy)

    def draw(self) -> None:
        """Render the current frame to the terminal."""
        self.renderer.clear_buffer()

        # Border
        self.renderer.draw_border(
            0, 0,
            self.renderer.width, self.renderer.height,
            Color.CYAN,
        )

        # Ball
        self.renderer.set_pixel(int(self.x), int(self.y), 'O', Color.BRIGHT_YELLOW)

        # HUD
        bx, by = int(self.x), int(self.y)
        self.renderer.draw_text(
            2, 1,
            f"Pos: ({bx:3d}, {by:3d})  Vel: ({self.vx:+.0f}, {self.vy:+.0f})",
            Color.WHITE,
        )
        self.renderer.draw_text(2, 2, "Arrows: change direction  ESC: exit", Color.GRAY)

        self.renderer.render()

    def run(self) -> None:
        """Main loop."""
        self.renderer.enter_fullscreen()
        last_time = time.time()
        try:
            while True:
                now = time.time()
                dt = min(now - last_time, 0.1)  # cap dt to avoid huge jumps
                last_time = now

                if not self.handle_input():
                    break
                self.update(dt)
                self.draw()
        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_bounce() -> None:
    """Entry point for the bouncing ball demo."""
    BouncingBall().run()
```

## Going Further

The Claugger source (`atari_style/demos/games/claugger.py`) is a good next read. It shows how to handle lanes, collision detection, scoring, lives, and a title/game-over screen — all built on exactly the same pattern you used here.

For analog joystick control (smooth rather than directional), look at Breakout (`atari_style/demos/games/breakout.py`), which uses `get_joystick_state()` to drive paddle position proportionally to the stick's X axis.
