"""Headless terminal renderer for video export.

Renders terminal-style character grids to PIL images, enabling video
export of terminal-based demos without actual terminal output.

Usage:
    from atari_style.core.headless_renderer import HeadlessRenderer

    renderer = HeadlessRenderer(width=80, height=24)
    renderer.set_pixel(10, 5, '●', 'green')
    renderer.draw_text(0, 0, 'Hello', 'cyan')

    # Get PIL Image
    img = renderer.to_image()
    img.save('frame.png')
"""

from typing import Optional, Tuple, Dict
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None


# ANSI color names to RGB values
# Based on typical terminal color schemes (close to Ubuntu/VSCode defaults)
ANSI_COLORS: Dict[str, Tuple[int, int, int]] = {
    # Standard colors
    'black': (0, 0, 0),
    'red': (205, 49, 49),
    'green': (13, 188, 121),
    'yellow': (229, 229, 16),
    'blue': (36, 114, 200),
    'magenta': (188, 63, 188),
    'cyan': (17, 168, 205),
    'white': (229, 229, 229),

    # Bright colors
    'bright_black': (102, 102, 102),
    'bright_red': (241, 76, 76),
    'bright_green': (35, 209, 139),
    'bright_yellow': (245, 245, 67),
    'bright_blue': (59, 142, 234),
    'bright_magenta': (214, 112, 214),
    'bright_cyan': (41, 184, 219),
    'bright_white': (255, 255, 255),
}

# Map Color class constants to RGB (blessed color names)
COLOR_NAME_MAP: Dict[str, str] = {
    # From Color class in renderer.py
    'black': 'black',
    'red': 'red',
    'green': 'green',
    'yellow': 'yellow',
    'blue': 'blue',
    'magenta': 'magenta',
    'cyan': 'cyan',
    'white': 'white',
    'bright_black': 'bright_black',
    'bright_red': 'bright_red',
    'bright_green': 'bright_green',
    'bright_yellow': 'bright_yellow',
    'bright_blue': 'bright_blue',
    'bright_magenta': 'bright_magenta',
    'bright_cyan': 'bright_cyan',
    'bright_white': 'bright_white',
}

# Default background color (dark terminal)
DEFAULT_BG_COLOR = (30, 30, 30)
DEFAULT_FG_COLOR = (229, 229, 229)


class HeadlessRenderer:
    """Renders terminal character grid to PIL images.

    Provides the same interface as Renderer but outputs to images
    instead of the terminal. Supports all standard drawing operations.
    """

    def __init__(
        self,
        width: int = 80,
        height: int = 24,
        char_width: int = 10,
        char_height: int = 20,
        font_path: Optional[str] = None,
        bg_color: Tuple[int, int, int] = DEFAULT_BG_COLOR,
    ):
        """Initialize headless renderer.

        Args:
            width: Character grid width (columns)
            height: Character grid height (rows)
            char_width: Pixel width per character
            char_height: Pixel height per character
            font_path: Path to TTF font file (uses default if None)
            bg_color: Background RGB color
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for HeadlessRenderer. Install with: pip install Pillow")

        self.width = width
        self.height = height
        self.char_width = char_width
        self.char_height = char_height
        self.bg_color = bg_color

        # Calculate pixel dimensions
        self.pixel_width = width * char_width
        self.pixel_height = height * char_height

        # Initialize buffers (same structure as Renderer)
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.color_buffer = [[None for _ in range(width)] for _ in range(height)]

        # Load font
        self.font = self._load_font(font_path)

    def _load_font(self, font_path: Optional[str]) -> 'ImageFont.FreeTypeFont':
        """Load monospace font for rendering."""
        font_size = self.char_height - 4  # Leave some padding

        if font_path and Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception:
                pass  # Fall through to defaults

        # Try common monospace fonts
        font_candidates = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
            '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf',
            '/usr/share/fonts/TTF/DejaVuSansMono.ttf',
            '/System/Library/Fonts/Menlo.ttc',  # macOS
            'C:/Windows/Fonts/consola.ttf',  # Windows
        ]

        for candidate in font_candidates:
            if Path(candidate).exists():
                try:
                    return ImageFont.truetype(candidate, font_size)
                except Exception:
                    continue

        # Fall back to default (may not be monospace)
        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def _color_to_rgb(self, color: Optional[str]) -> Tuple[int, int, int]:
        """Convert color name to RGB tuple."""
        if color is None:
            return DEFAULT_FG_COLOR

        # Normalize color name
        color_lower = color.lower().replace('-', '_')

        # Direct lookup
        if color_lower in ANSI_COLORS:
            return ANSI_COLORS[color_lower]

        # Try mapped name
        mapped = COLOR_NAME_MAP.get(color_lower)
        if mapped and mapped in ANSI_COLORS:
            return ANSI_COLORS[mapped]

        # Default to white
        return DEFAULT_FG_COLOR

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
        """No-op for headless mode (compatibility with Renderer)."""
        pass

    def enter_fullscreen(self):
        """No-op for headless mode."""
        pass

    def exit_fullscreen(self):
        """No-op for headless mode."""
        pass

    def clear_screen(self):
        """Clear buffer (alias for clear_buffer in headless mode)."""
        self.clear_buffer()

    def to_image(self) -> 'Image.Image':
        """Render the buffer to a PIL Image.

        Returns:
            PIL Image with rendered terminal content
        """
        # Create image with background color
        img = Image.new('RGB', (self.pixel_width, self.pixel_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Render each character
        for y in range(self.height):
            for x in range(self.width):
                char = self.buffer[y][x]
                if char == ' ':
                    continue  # Skip spaces for performance

                color = self.color_buffer[y][x]
                rgb = self._color_to_rgb(color)

                # Calculate pixel position
                px = x * self.char_width
                py = y * self.char_height

                # Draw character
                if self.font:
                    draw.text((px, py), char, font=self.font, fill=rgb)
                else:
                    # Fallback: draw a colored rectangle for non-space chars
                    if char != ' ':
                        draw.rectangle(
                            [px + 2, py + 2, px + self.char_width - 2, py + self.char_height - 2],
                            fill=rgb
                        )

        return img

    def save_frame(self, path: str):
        """Render and save frame to file.

        Args:
            path: Output file path (PNG, JPEG, etc.)
        """
        img = self.to_image()
        img.save(path)


class HeadlessRendererFactory:
    """Factory for creating HeadlessRenderer with video format presets."""

    @staticmethod
    def for_resolution(
        width: int,
        height: int,
        char_columns: int = 80,
        char_rows: int = 24,
        **kwargs
    ) -> HeadlessRenderer:
        """Create renderer targeting specific pixel resolution.

        Automatically calculates character size to fill the resolution.

        Args:
            width: Target pixel width
            height: Target pixel height
            char_columns: Number of character columns
            char_rows: Number of character rows
            **kwargs: Additional HeadlessRenderer arguments
        """
        char_width = width // char_columns
        char_height = height // char_rows

        return HeadlessRenderer(
            width=char_columns,
            height=char_rows,
            char_width=char_width,
            char_height=char_height,
            **kwargs
        )

    @staticmethod
    def for_youtube_shorts(char_columns: int = 60, char_rows: int = 80) -> HeadlessRenderer:
        """Create renderer for YouTube Shorts (1080x1920)."""
        return HeadlessRendererFactory.for_resolution(
            1080, 1920, char_columns, char_rows
        )

    @staticmethod
    def for_1080p(char_columns: int = 120, char_rows: int = 45) -> HeadlessRenderer:
        """Create renderer for 1080p (1920x1080)."""
        return HeadlessRendererFactory.for_resolution(
            1920, 1080, char_columns, char_rows
        )

    @staticmethod
    def for_720p(char_columns: int = 100, char_rows: int = 38) -> HeadlessRenderer:
        """Create renderer for 720p (1280x720)."""
        return HeadlessRendererFactory.for_resolution(
            1280, 720, char_columns, char_rows
        )
