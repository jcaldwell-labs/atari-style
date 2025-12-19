"""Zone renderer for outputting ANSI frames to stdout.

This renderer is designed for embedding atari-style demos in zones (like my-grid).
Instead of using blessed Terminal, it outputs raw ANSI escape codes to stdout
for capture by parent process.
"""

from typing import Optional

# ANSI color codes
ANSI_COLORS = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bright_black': '\033[90m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',
}

ANSI_RESET = '\033[0m'


class ZoneRenderer:
    """Renderer that outputs ANSI frames to stdout for zone embedding."""

    def __init__(self, width: int = 80, height: int = 24):
        """Initialize zone renderer with fixed dimensions.

        Args:
            width: Character width of the zone
            height: Character height of the zone
        """
        self.width = width
        self.height = height
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.color_buffer = [[None for _ in range(width)] for _ in range(height)]

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
        """Render the buffer as ANSI text to stdout."""
        lines = []
        for y in range(self.height):
            line_parts = []
            current_color = None

            for x in range(self.width):
                char = self.buffer[y][x]
                color = self.color_buffer[y][x]

                # Change color if needed
                if color != current_color:
                    if current_color is not None:
                        line_parts.append(ANSI_RESET)
                    if color is not None and color in ANSI_COLORS:
                        line_parts.append(ANSI_COLORS[color])
                    current_color = color

                line_parts.append(char)

            # Reset color at end of line
            if current_color is not None:
                line_parts.append(ANSI_RESET)

            lines.append(''.join(line_parts))

        # Output all lines with newlines
        print('\n'.join(lines), flush=True)
        print('', flush=True)  # Extra newline as frame separator

    # Stub methods for compatibility with Renderer API
    def enter_fullscreen(self):
        """No-op for zone mode."""
        pass

    def exit_fullscreen(self):
        """No-op for zone mode."""
        pass

    def clear_screen(self):
        """No-op for zone mode."""
        pass

    def save_screenshot(self, path: str) -> bool:
        """Not supported in zone mode."""
        return False


# Color class for compatibility
class Color:
    """Color constants matching renderer.py"""
    BLACK = 'black'
    RED = 'red'
    GREEN = 'green'
    YELLOW = 'yellow'
    BLUE = 'blue'
    MAGENTA = 'magenta'
    CYAN = 'cyan'
    WHITE = 'white'
    BRIGHT_BLACK = 'bright_black'
    BRIGHT_RED = 'bright_red'
    BRIGHT_GREEN = 'bright_green'
    BRIGHT_YELLOW = 'bright_yellow'
    BRIGHT_BLUE = 'bright_blue'
    BRIGHT_MAGENTA = 'bright_magenta'
    BRIGHT_CYAN = 'bright_cyan'
    BRIGHT_WHITE = 'bright_white'
