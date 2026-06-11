"""Terminal rendering engine using blessed."""

from blessed import Terminal
from typing import Tuple, Optional
import time


class Renderer:
    """Handles terminal rendering with double buffering."""

    def __init__(self):
        self.term = Terminal()
        self.width = self.term.width
        self.height = self.term.height
        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.color_buffer = [[None for _ in range(self.width)] for _ in range(self.height)]

    def clear_buffer(self):
        """Clear the rendering buffer."""
        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.color_buffer = [[None for _ in range(self.width)] for _ in range(self.height)]

    def set_pixel(self, x: int, y: int, char: str = '█', color: Optional[str] = None):
        """Set a character in the buffer at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color

    def draw_text(self, x: int, y: int, text: str, color: Optional[str] = None):
        """Draw text at the given position."""
        for i, char in enumerate(text):
            self.set_pixel(x + i, y, char, color)

    def draw_box(self, x: int, y: int, width: int, height: int, char: str = '█', color: Optional[str] = None):
        """Draw a filled box."""
        for dy in range(height):
            for dx in range(width):
                self.set_pixel(x + dx, y + dy, char, color)

    def draw_border(self, x: int, y: int, width: int, height: int, color: Optional[str] = None):
        """Draw a border box."""
        # Top and bottom
        for dx in range(width):
            self.set_pixel(x + dx, y, '─', color)
            self.set_pixel(x + dx, y + height - 1, '─', color)
        # Left and right
        for dy in range(height):
            self.set_pixel(x, y + dy, '│', color)
            self.set_pixel(x + width - 1, y + dy, '│', color)
        # Corners
        self.set_pixel(x, y, '┌', color)
        self.set_pixel(x + width - 1, y, '┐', color)
        self.set_pixel(x, y + height - 1, '└', color)
        self.set_pixel(x + width - 1, y + height - 1, '┘', color)

    def render(self):
        """Render the buffer to the terminal."""
        output = []
        for y in range(self.height):
            for x in range(self.width):
                char = self.buffer[y][x]
                color = self.color_buffer[y][x]

                if color:
                    output.append(self.term.move_xy(x, y) + getattr(self.term, color, '')(char))
                else:
                    output.append(self.term.move_xy(x, y) + char)

        print(''.join(output), end='', flush=True)

    def enter_fullscreen(self):
        """Enter fullscreen mode."""
        print(self.term.enter_fullscreen() + self.term.hide_cursor(), end='', flush=True)

    def exit_fullscreen(self):
        """Exit fullscreen mode."""
        print(self.term.exit_fullscreen() + self.term.normal_cursor(), end='', flush=True)

    def clear_screen(self):
        """Clear the terminal screen."""
        print(self.term.home + self.term.clear, end='', flush=True)


class Color:
    """Color constants for easy access."""
    BLACK = 'black'
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'
    YELLOW = 'yellow'
    MAGENTA = 'magenta'
    CYAN = 'cyan'
    WHITE = 'white'
    DARK_GRAY = 'bright_black'  # Bright black appears as dark gray
    BRIGHT_RED = 'bright_red'
    BRIGHT_GREEN = 'bright_green'
    BRIGHT_BLUE = 'bright_blue'
    BRIGHT_YELLOW = 'bright_yellow'
    BRIGHT_MAGENTA = 'bright_magenta'
    BRIGHT_CYAN = 'bright_cyan'
    BRIGHT_WHITE = 'bright_white'
