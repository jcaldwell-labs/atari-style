#!/usr/bin/env python3
"""Lissajous Explorer - Interactive pattern navigator with settling transitions.

Navigate between stable Lissajous patterns using joystick/keyboard/mouse.
Watch the curve morph through chaotic intermediate states as it settles
into recognizable mathematical figures.

The key mechanic: your selection can move fast, but the actual parameters
settle slowly - creating a "navigation through chaos" effect.
"""

import math
import time
import pygame
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ....core.renderer import Renderer, Color
from ....core.input_handler import InputHandler, InputType


# =============================================================================
# STABLE PATTERNS - The "destinations" in parameter space
# =============================================================================

@dataclass
class StablePattern:
    """A stable Lissajous pattern at specific parameter ratios."""
    name: str
    a: float          # X frequency
    b: float          # Y frequency
    delta: float      # Phase offset (radians)
    description: str  # Short description
    complexity: int   # 1-5 rating for sorting/display

    @property
    def ratio_str(self) -> str:
        """Human-readable ratio string."""
        return f"{int(self.a)}:{int(self.b)}"


# All recognizable stable patterns
STABLE_PATTERNS = [
    StablePattern("Circle", 1.0, 1.0, math.pi/2, "Perfect loop", 1),
    StablePattern("Ellipse", 1.0, 1.0, math.pi/4, "Tilted oval", 1),
    StablePattern("Figure-8", 1.0, 2.0, 0, "Infinity symbol", 2),
    StablePattern("Bow-tie", 1.0, 2.0, math.pi/2, "Crossed loops", 2),
    StablePattern("Parabola", 1.0, 2.0, math.pi/4, "Open curve", 2),
    StablePattern("Trefoil", 2.0, 3.0, 0, "Three leaves", 3),
    StablePattern("Fish", 2.0, 3.0, math.pi/2, "Swimming shape", 3),
    StablePattern("Quatrefoil", 3.0, 4.0, 0, "Four petals", 4),
    StablePattern("Butterfly", 3.0, 4.0, math.pi/4, "Wing pattern", 4),
    StablePattern("Star-5", 2.0, 5.0, 0, "Five points", 4),
    StablePattern("Pentagram", 3.0, 5.0, 0, "Complex star", 5),
    StablePattern("Hexafoil", 5.0, 6.0, 0, "Six petals", 5),
]


# =============================================================================
# COLOR THEMES
# =============================================================================

THEMES = {
    'ocean': {
        'palette': ['blue', 'cyan', 'bright_cyan', 'green', 'bright_blue', 'white'],
        'menu_bg': Color.BLUE,
        'menu_fg': Color.CYAN,
        'menu_sel': Color.BRIGHT_CYAN,
        'menu_dim': Color.BLUE,
    },
    'desert': {
        'palette': ['bright_yellow', 'yellow', 'red', 'bright_red', 'magenta', 'white'],
        'menu_bg': Color.RED,
        'menu_fg': Color.YELLOW,
        'menu_sel': Color.BRIGHT_YELLOW,
        'menu_dim': Color.RED,
    },
    'forest': {
        'palette': ['green', 'bright_green', 'yellow', 'cyan', 'blue', 'white'],
        'menu_bg': Color.GREEN,
        'menu_fg': Color.BRIGHT_GREEN,
        'menu_sel': Color.BRIGHT_WHITE,
        'menu_dim': Color.GREEN,
    },
    'mountain': {
        'palette': ['white', 'bright_cyan', 'cyan', 'blue', 'magenta', 'bright_blue'],
        'menu_bg': Color.BLUE,
        'menu_fg': Color.WHITE,
        'menu_sel': Color.BRIGHT_WHITE,
        'menu_dim': Color.CYAN,
    },
}


# =============================================================================
# PARAMETER SMOOTHER - The settling mechanic
# =============================================================================

class ParameterSmoother:
    """Smoothly interpolates parameters with configurable settling time.

    This creates the "chaos navigation" effect - selection moves fast,
    but actual parameters settle slowly through intermediate states.
    """

    def __init__(self, settling_time: float = 1.5):
        """
        Args:
            settling_time: Seconds to reach 95% of target value
        """
        self.settling_time = settling_time

        # Current actual values (what's being rendered)
        self.current_a = 1.0
        self.current_b = 1.0
        self.current_delta = math.pi / 2

        # Target values (where we're heading)
        self.target_a = 1.0
        self.target_b = 1.0
        self.target_delta = math.pi / 2

        # Velocity for momentum-based smoothing
        self.vel_a = 0.0
        self.vel_b = 0.0
        self.vel_delta = 0.0

    def set_target(self, pattern: StablePattern):
        """Set new target pattern to settle toward."""
        self.target_a = pattern.a
        self.target_b = pattern.b
        self.target_delta = pattern.delta

    def update(self, dt: float):
        """Update current values toward target with smooth settling.

        Uses critically damped spring physics for natural motion.
        """
        # Spring constant derived from settling time
        # For critically damped: omega = 4 / settling_time (reaches 98% in settling_time)
        omega = 4.0 / self.settling_time
        damping = 2.0 * omega  # Critical damping

        # Update each parameter with spring physics
        def spring_update(current, target, velocity, omega, damping, dt):
            error = target - current
            accel = omega * omega * error - damping * velocity
            new_vel = velocity + accel * dt
            new_val = current + new_vel * dt
            return new_val, new_vel

        self.current_a, self.vel_a = spring_update(
            self.current_a, self.target_a, self.vel_a, omega, damping, dt)
        self.current_b, self.vel_b = spring_update(
            self.current_b, self.target_b, self.vel_b, omega, damping, dt)
        self.current_delta, self.vel_delta = spring_update(
            self.current_delta, self.target_delta, self.vel_delta, omega, damping, dt)

    def get_settling_progress(self) -> float:
        """Return 0-1 indicating how settled we are (1 = fully stable)."""
        error_a = abs(self.target_a - self.current_a)
        error_b = abs(self.target_b - self.current_b)
        error_d = abs(self.target_delta - self.current_delta)

        # Normalize errors (typical range is 0-5 for a/b, 0-pi for delta)
        total_error = error_a / 5.0 + error_b / 5.0 + error_d / math.pi

        # Convert to 0-1 progress (0 = far, 1 = settled)
        return max(0.0, 1.0 - total_error)

    def is_settled(self, threshold: float = 0.95) -> bool:
        """Check if we've settled close enough to target."""
        return self.get_settling_progress() >= threshold


# =============================================================================
# LISSAJOUS RENDERER (for display region)
# =============================================================================

# Map color names to Color enum
COLOR_MAP = {
    'red': Color.RED,
    'green': Color.GREEN,
    'yellow': Color.YELLOW,
    'blue': Color.BLUE,
    'magenta': Color.MAGENTA,
    'cyan': Color.CYAN,
    'white': Color.WHITE,
    'bright_red': Color.BRIGHT_RED,
    'bright_green': Color.BRIGHT_GREEN,
    'bright_yellow': Color.BRIGHT_YELLOW,
    'bright_blue': Color.BRIGHT_BLUE,
    'bright_magenta': Color.BRIGHT_MAGENTA,
    'bright_cyan': Color.BRIGHT_CYAN,
    'bright_white': Color.BRIGHT_WHITE,
}


def draw_lissajous_region(renderer: Renderer,
                          x: int, y: int, width: int, height: int,
                          t: float, a: float, b: float, delta: float,
                          palette: List[str], trail_length: int = 6,
                          resolution_scale: float = 1.0):
    """Draw Lissajous curve in a bounded region of the screen.

    Args:
        resolution_scale: Multiplier for point density (1.75 = 75% more points)
    """
    cx = x + width // 2
    cy = y + height // 2
    scale_x = width // 3
    scale_y = height // 3

    # Scale points with resolution for denser curves
    points = int(500 * resolution_scale)
    trail_chars = ['●', '○', '◦', '·', '.']

    # Draw trails
    for trail in range(trail_length - 1, 0, -1):
        trail_t = t - trail * 0.025

        for i in range(points):
            angle = (i / points) * 2 * math.pi

            px = math.sin(a * angle + trail_t)
            py = math.sin(b * angle + delta + trail_t * 0.5)

            screen_x = int(cx + px * scale_x * 1.4)
            screen_y = int(cy + py * scale_y * 0.85)

            # Clip to region
            if x <= screen_x < x + width and y <= screen_y < y + height:
                color_idx = int((i / points) * len(palette))
                color_name = palette[color_idx % len(palette)]
                color = COLOR_MAP.get(color_name, Color.WHITE)
                char_idx = min(trail, len(trail_chars) - 1)
                renderer.set_pixel(screen_x, screen_y, trail_chars[char_idx], color)

    # Draw current curve (brightest)
    for i in range(points):
        angle = (i / points) * 2 * math.pi

        px = math.sin(a * angle + t)
        py = math.sin(b * angle + delta + t * 0.5)

        screen_x = int(cx + px * scale_x * 1.4)
        screen_y = int(cy + py * scale_y * 0.85)

        if x <= screen_x < x + width and y <= screen_y < y + height:
            color_idx = int((i / points) * len(palette))
            color_name = palette[color_idx % len(palette)]
            color = COLOR_MAP.get(color_name, Color.WHITE)
            renderer.set_pixel(screen_x, screen_y, '●', color)


# =============================================================================
# MAIN EXPLORER CLASS
# =============================================================================

class LissajousExplorer:
    """Interactive Lissajous pattern explorer with settling transitions."""

    def __init__(self, scale_factor: float = 1.75):
        """
        Args:
            scale_factor: Resolution multiplier (1.75 = 75% more resolution)
        """
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

        # Apply scale factor for higher resolution
        # This gives us more character cells to work with
        self.scale_factor = scale_factor
        base_width = self.renderer.width
        base_height = self.renderer.height

        # Effective resolution (for calculations)
        self.eff_width = int(base_width * scale_factor)
        self.eff_height = int(base_height * scale_factor)

        # Layout - display region on left, menu on right
        # Display gets 70% of width
        self.display_width = int(base_width * 0.70)
        self.display_height = base_height - 4  # Leave room for status
        self.display_x = 0
        self.display_y = 2

        self.menu_x = self.display_width + 1
        self.menu_width = base_width - self.menu_x - 1

        # Pattern selection
        self.patterns = STABLE_PATTERNS
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_items = self.renderer.height - 8

        # Parameter smoother (the settling mechanic!)
        self.smoother = ParameterSmoother(settling_time=1.5)
        self.smoother.set_target(self.patterns[0])

        # Theme
        self.current_theme = 'ocean'
        self.theme = THEMES[self.current_theme]

        # Animation time
        self.t = 0.0

        # Input debouncing
        self.last_input_time = 0.0
        self.input_cooldown = 0.12  # Seconds between inputs

        # Properties panel (read-only for now)
        self.properties = {
            'Theme': self.current_theme,
            'Settling': '1.5s',
            'Points': '400',
        }

    def handle_input(self, dt: float):
        """Handle navigation input."""
        current_time = time.time()

        # Get input
        inp = self.input_handler.get_input(timeout=0.01)

        # Check joystick for analog navigation
        joy_moved = False
        if self.input_handler.joystick_initialized:
            x, y = self.input_handler.get_joystick_state()

            if current_time - self.last_input_time > self.input_cooldown:
                if y < -0.5:  # Up
                    self.move_selection(-1)
                    self.last_input_time = current_time
                    joy_moved = True
                elif y > 0.5:  # Down
                    self.move_selection(1)
                    self.last_input_time = current_time
                    joy_moved = True

        # Keyboard input (if not already moved by joystick)
        if not joy_moved and current_time - self.last_input_time > self.input_cooldown:
            if inp == InputType.UP:
                self.move_selection(-1)
                self.last_input_time = current_time
            elif inp == InputType.DOWN:
                self.move_selection(1)
                self.last_input_time = current_time

        if inp == InputType.QUIT:
            self.running = False

    def move_selection(self, delta: int):
        """Move selection and update target pattern."""
        old_index = self.selected_index
        self.selected_index = max(0, min(len(self.patterns) - 1, self.selected_index + delta))

        if self.selected_index != old_index:
            # Update target - smoother will handle the settling
            self.smoother.set_target(self.patterns[self.selected_index])

            # Adjust scroll to keep selection visible
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
            elif self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1

    def update(self, dt: float):
        """Update animation and settling."""
        self.t += dt * 2.0  # Animation speed
        self.smoother.update(dt)

    def draw_display_region(self):
        """Draw the Lissajous visualization area."""
        # Border
        self.renderer.draw_border(
            self.display_x, self.display_y - 1,
            self.display_width, self.display_height + 2,
            Color.CYAN
        )

        # Draw curve with current (settling) parameters
        palette_colors = self.theme['palette']
        draw_lissajous_region(
            self.renderer,
            self.display_x + 1, self.display_y,
            self.display_width - 2, self.display_height,
            self.t,
            self.smoother.current_a,
            self.smoother.current_b,
            self.smoother.current_delta,
            palette_colors,
            trail_length=8,
            resolution_scale=self.scale_factor
        )

        # Current parameters display
        params = f"a={self.smoother.current_a:.2f} b={self.smoother.current_b:.2f} δ={self.smoother.current_delta:.2f}"
        self.renderer.draw_text(2, 0, params, Color.YELLOW)

        # Settling indicator
        progress = self.smoother.get_settling_progress()
        if progress < 0.95:
            bar_width = 20
            filled = int(progress * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            self.renderer.draw_text(self.display_width - 25, 0, f"[{bar}]", Color.CYAN)
        else:
            self.renderer.draw_text(self.display_width - 12, 0, "● STABLE", Color.BRIGHT_GREEN)

    def draw_menu(self):
        """Draw the pattern selection menu."""
        menu_y = 2

        # Title
        self.renderer.draw_text(self.menu_x + 1, menu_y, "PATTERNS", Color.BRIGHT_WHITE)
        menu_y += 2

        # Pattern list
        for i in range(self.visible_items):
            idx = self.scroll_offset + i
            if idx >= len(self.patterns):
                break

            pattern = self.patterns[idx]
            is_selected = idx == self.selected_index

            # Selection indicator
            if is_selected:
                prefix = "▶ "
                color = self.theme['menu_sel']
            else:
                prefix = "  "
                color = self.theme['menu_fg']

            # Pattern name and ratio
            text = f"{prefix}{pattern.name}"
            self.renderer.draw_text(self.menu_x, menu_y + i, text, color)

            # Ratio on the right
            ratio = pattern.ratio_str
            self.renderer.draw_text(
                self.menu_x + self.menu_width - len(ratio) - 1,
                menu_y + i, ratio,
                Color.YELLOW if is_selected else self.theme['menu_dim']
            )

        # Scroll indicators
        if self.scroll_offset > 0:
            self.renderer.draw_text(self.menu_x + self.menu_width // 2, menu_y - 1, "▲", Color.CYAN)
        if self.scroll_offset + self.visible_items < len(self.patterns):
            self.renderer.draw_text(
                self.menu_x + self.menu_width // 2,
                menu_y + self.visible_items, "▼", Color.CYAN
            )

        # Selected pattern info
        info_y = self.renderer.height - 5
        pattern = self.patterns[self.selected_index]

        self.renderer.draw_text(self.menu_x, info_y, "─" * self.menu_width, Color.CYAN)
        self.renderer.draw_text(self.menu_x + 1, info_y + 1, pattern.description, Color.WHITE)

        complexity_stars = "★" * pattern.complexity + "☆" * (5 - pattern.complexity)
        self.renderer.draw_text(self.menu_x + 1, info_y + 2, f"Complexity: {complexity_stars}", Color.YELLOW)

    def draw_controls(self):
        """Draw control hints."""
        y = self.renderer.height - 1
        controls = "↑↓/Joystick: Navigate  |  ESC: Exit"
        self.renderer.draw_text(2, y, controls, Color.CYAN)

        # Theme indicator
        theme_text = f"Theme: {self.current_theme}"
        self.renderer.draw_text(self.renderer.width - len(theme_text) - 2, y, theme_text, Color.MAGENTA)

    def draw(self):
        """Render everything."""
        self.renderer.clear_buffer()

        self.draw_display_region()
        self.draw_menu()
        self.draw_controls()

        self.renderer.render()

    def run(self):
        """Main loop."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            last_time = time.time()

            while self.running:
                current_time = time.time()
                dt = min(current_time - last_time, 0.1)
                last_time = current_time

                self.handle_input(dt)
                self.update(dt)
                self.draw()

                time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_lissajous_explorer():
    """Entry point."""
    explorer = LissajousExplorer()
    explorer.run()


if __name__ == '__main__':
    run_lissajous_explorer()
