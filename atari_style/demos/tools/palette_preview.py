#!/usr/bin/env python3
"""Palette preview tool - visualize atari-style color palettes.

Displays all defined palettes with sample text and block characters.
Useful for choosing palettes and verifying terminal color support.

Usage:
    python -m atari_style.demos.tools.palette_preview
"""

import time
from ...core.renderer import Renderer, Color, Palette
from ...core.input_handler import InputHandler, InputType


class PalettePreview:
    """Interactive palette preview tool."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True
        self.selected_palette = 0
        self.palette_names = list(Palette.ALL.keys())

    def draw_color_block(self, x: int, y: int, color: str, label: str):
        """Draw a color sample block with label."""
        # Block characters
        self.renderer.draw_text(x, y, '████', color)
        self.renderer.draw_text(x, y + 1, '████', color)
        # Label
        self.renderer.draw_text(x, y + 2, label[:4].center(4), Color.WHITE)

    def draw_all_colors(self, start_y: int):
        """Draw all 16 ANSI colors."""
        colors = [
            ('black', 'BLK'), ('red', 'RED'), ('green', 'GRN'), ('yellow', 'YEL'),
            ('blue', 'BLU'), ('magenta', 'MAG'), ('cyan', 'CYN'), ('white', 'WHT'),
        ]
        bright_colors = [
            ('bright_black', 'GRY'), ('bright_red', 'BRD'), ('bright_green', 'BGN'),
            ('bright_yellow', 'BYL'), ('bright_blue', 'BBL'), ('bright_magenta', 'BMG'),
            ('bright_cyan', 'BCN'), ('bright_white', 'BWH'),
        ]

        x = 2
        self.renderer.draw_text(x, start_y, 'Standard Colors:', Color.BRIGHT_WHITE)
        for i, (color, label) in enumerate(colors):
            self.draw_color_block(x + i * 6, start_y + 1, color, label)

        self.renderer.draw_text(x, start_y + 5, 'Bright Colors:', Color.BRIGHT_WHITE)
        for i, (color, label) in enumerate(bright_colors):
            self.draw_color_block(x + i * 6, start_y + 6, color, label)

    def draw_palette(self, name: str, palette: list, x: int, y: int, selected: bool = False):
        """Draw a named palette."""
        # Palette name
        prefix = '>' if selected else ' '
        color = Color.BRIGHT_CYAN if selected else Color.WHITE
        self.renderer.draw_text(x, y, f"{prefix} {name.upper()}", color)

        # Color swatches
        for i, c in enumerate(palette):
            self.renderer.draw_text(x + 2 + i * 3, y + 1, '██', c)

        # Sample gradient text
        sample = "ATARI-STYLE"
        for i, char in enumerate(sample):
            c = palette[i % len(palette)]
            self.renderer.draw_text(x + 2 + i, y + 2, char, c)

    def draw(self):
        """Render the palette preview."""
        self.renderer.clear_buffer()
        width = self.renderer.width
        height = self.renderer.height

        # Title
        title = "PALETTE PREVIEW"
        self.renderer.draw_text((width - len(title)) // 2, 1, title, Color.BRIGHT_CYAN)
        self.renderer.draw_text((width - 40) // 2, 2, "See AESTHETIC.md for usage guidelines", Color.CYAN)

        # Draw all 16 colors
        self.draw_all_colors(4)

        # Draw named palettes
        self.renderer.draw_text(2, 15, 'Named Palettes (UP/DOWN to select):', Color.BRIGHT_WHITE)

        y = 17
        for i, name in enumerate(self.palette_names):
            palette = Palette.ALL[name]
            selected = (i == self.selected_palette)
            self.draw_palette(name, palette, 2, y, selected)
            y += 4

        # Block character reference
        ref_y = height - 6
        self.renderer.draw_text(2, ref_y, 'Block Characters:', Color.BRIGHT_WHITE)
        blocks = "█ ▀ ▄ ▌ ▐ ░ ▒ ▓"
        self.renderer.draw_text(2, ref_y + 1, blocks, Color.BRIGHT_GREEN)

        # Box drawing reference
        self.renderer.draw_text(30, ref_y, 'Box Drawing:', Color.BRIGHT_WHITE)
        self.renderer.draw_text(30, ref_y + 1, '┌─┬─┐', Color.BRIGHT_CYAN)
        self.renderer.draw_text(30, ref_y + 2, '├─┼─┤', Color.BRIGHT_CYAN)
        self.renderer.draw_text(30, ref_y + 3, '└─┴─┘', Color.BRIGHT_CYAN)

        # Controls
        self.renderer.draw_text(2, height - 2, "UP/DOWN: Select palette  Q/ESC: Exit", Color.YELLOW)

        self.renderer.render()

    def handle_input(self):
        """Handle user input."""
        input_type = self.input_handler.get_input(timeout=0.1)

        if input_type == InputType.QUIT:
            self.running = False
        elif input_type == InputType.UP:
            self.selected_palette = (self.selected_palette - 1) % len(self.palette_names)
        elif input_type == InputType.DOWN:
            self.selected_palette = (self.selected_palette + 1) % len(self.palette_names)

    def run(self):
        """Run the palette preview."""
        try:
            self.renderer.enter_fullscreen()

            while self.running:
                self.draw()
                self.handle_input()
                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()


def run_palette_preview():
    """Entry point for palette preview."""
    preview = PalettePreview()
    preview.run()


if __name__ == '__main__':
    run_palette_preview()
