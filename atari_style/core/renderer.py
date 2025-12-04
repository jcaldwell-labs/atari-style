"""Terminal rendering engine using blessed."""

from blessed import Terminal
from typing import Tuple, Optional
import time
import os


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

    def save_screenshot(self, path: str) -> bool:
        """Export current buffer as PNG image for thumbnails.

        Args:
            path: Output path for PNG file

        Returns:
            True if successful, False otherwise
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("Pillow required for screenshots: pip install Pillow")
            return False

        # Character dimensions (approximate for monospace)
        char_width = 10
        char_height = 20

        img_width = self.width * char_width
        img_height = self.height * char_height

        # Create image with dark background (Dracula theme)
        img = Image.new('RGB', (img_width, img_height), (30, 30, 46))
        draw = ImageDraw.Draw(img)

        # Try to use a monospace font
        try:
            # Try common monospace font paths
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/System/Library/Fonts/Monaco.dfont",  # macOS
                "C:\\Windows\\Fonts\\consola.ttf",  # Windows
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 16)
                    break
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Terminal color name to RGB mapping
        color_map = {
            'red': (205, 49, 49),
            'green': (13, 188, 121),
            'blue': (36, 114, 200),
            'yellow': (229, 229, 16),
            'magenta': (188, 63, 188),
            'cyan': (17, 168, 205),
            'white': (229, 229, 229),
            'bright_red': (241, 76, 76),
            'bright_green': (35, 209, 139),
            'bright_blue': (59, 142, 234),
            'bright_yellow': (245, 245, 67),
            'bright_magenta': (214, 112, 214),
            'bright_cyan': (41, 184, 219),
            'bright_white': (255, 255, 255),
        }

        # Render buffer to image
        for y in range(self.height):
            for x in range(self.width):
                char = self.buffer[y][x]
                if char == ' ':
                    continue  # Skip empty spaces for performance

                color_name = self.color_buffer[y][x]
                if color_name and color_name in color_map:
                    color = color_map[color_name]
                else:
                    color = (229, 229, 229)  # Default white

                draw.text((x * char_width, y * char_height), char, font=font, fill=color)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)

        img.save(path)
        return True


class Color:
    """Color constants for easy access.

    See AESTHETIC.md for the atari-style color philosophy.
    """
    # Standard colors
    BLACK = 'black'
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'
    YELLOW = 'yellow'
    MAGENTA = 'magenta'
    CYAN = 'cyan'
    WHITE = 'white'

    # Bright colors
    BRIGHT_BLACK = 'bright_black'  # gray
    BRIGHT_RED = 'bright_red'
    BRIGHT_GREEN = 'bright_green'
    BRIGHT_BLUE = 'bright_blue'
    BRIGHT_YELLOW = 'bright_yellow'
    BRIGHT_MAGENTA = 'bright_magenta'
    BRIGHT_CYAN = 'bright_cyan'
    BRIGHT_WHITE = 'bright_white'

    # Aliases
    GRAY = 'bright_black'


class Palette:
    """Named color palettes for atari-style visuals.

    Each palette is a list of color names designed to work together.
    See AESTHETIC.md for palette usage guidelines.
    """

    # Classic Atari - the original 8-bit feeling
    CLASSIC = [
        Color.BRIGHT_CYAN, Color.BRIGHT_GREEN, Color.BRIGHT_YELLOW,
        Color.BRIGHT_RED, Color.BRIGHT_MAGENTA, Color.WHITE
    ]

    # Plasma - smooth rainbow for mathematical visualizations
    PLASMA = [
        Color.BLUE, Color.CYAN, Color.GREEN, Color.YELLOW,
        Color.RED, Color.MAGENTA
    ]

    # Midnight - dark, atmospheric, mysterious
    MIDNIGHT = [
        Color.BLUE, Color.MAGENTA, Color.BRIGHT_MAGENTA,
        Color.CYAN, Color.BRIGHT_CYAN, Color.WHITE
    ]

    # Forest - organic, natural, growing
    FOREST = [
        Color.GREEN, Color.BRIGHT_GREEN, Color.YELLOW,
        Color.CYAN, Color.BRIGHT_WHITE
    ]

    # Fire - intense, dynamic, dangerous
    FIRE = [
        Color.RED, Color.BRIGHT_RED, Color.YELLOW,
        Color.BRIGHT_YELLOW, Color.WHITE
    ]

    # Ocean - deep, calm, flowing
    OCEAN = [
        Color.BLUE, Color.CYAN, Color.BRIGHT_CYAN,
        Color.GREEN, Color.BRIGHT_BLUE, Color.WHITE
    ]

    # Monochrome - classic green-screen terminal
    MONOCHROME = [
        Color.GREEN, Color.BRIGHT_GREEN, Color.BRIGHT_WHITE
    ]

    # All available palettes for iteration
    ALL = {
        'classic': CLASSIC,
        'plasma': PLASMA,
        'midnight': MIDNIGHT,
        'forest': FOREST,
        'fire': FIRE,
        'ocean': OCEAN,
        'monochrome': MONOCHROME,
    }

    @classmethod
    def get(cls, name: str) -> list:
        """Get a palette by name."""
        return cls.ALL.get(name.lower(), cls.CLASSIC)
