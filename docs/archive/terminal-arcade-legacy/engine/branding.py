"""Branding and logo assets for Terminal Arcade.

Provides ASCII art logos, credits, and GitHub attribution.
"""

from typing import Optional
from .renderer import Renderer, Color


class Brand:
    """Terminal Arcade branding assets."""

    # Main Terminal Arcade logo (large)
    LOGO_LARGE = [
        "████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     ",
        "╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     ",
        "   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     ",
        "   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     ",
        "   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗",
        "   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝",
        "                                                                   ",
        " █████╗ ██████╗  ██████╗ █████╗ ██████╗ ███████╗                 ",
        "██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝                 ",
        "███████║██████╔╝██║     ███████║██║  ██║█████╗                   ",
        "██╔══██║██╔══██╗██║     ██╔══██║██║  ██║██╔══╝                   ",
        "██║  ██║██║  ██║╚██████╗██║  ██║██████╔╝███████╗                 ",
        "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝                 ",
    ]

    # Compact logo for headers
    LOGO_COMPACT = [
        "▀█▀ █▀▀ █▀█ █▀▄▀█ █ █▄░█ ▄▀█ █░░   ▄▀█ █▀█ █▀▀ ▄▀█ █▀▄ █▀▀",
        "░█░ ██▄ █▀▄ █░▀░█ █ █░▀█ █▀█ █▄▄   █▀█ █▀▄ █▄▄ █▀█ █▄▀ ██▄",
    ]

    # Retro arcade cabinet logo
    LOGO_CABINET = [
        "    ╔════════════════════════════╗",
        "    ║  ░▒▓ TERMINAL ARCADE ▓▒░  ║",
        "    ╠════════════════════════════╣",
        "    ║  ┌──────────────────────┐  ║",
        "    ║  │  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄  │  ║",
        "    ║  │  █ PRESS START █  │  ║",
        "    ║  │  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  │  ║",
        "    ║  └──────────────────────┘  ║",
        "    ║     🕹️              🕹️      ║",
        "    ╚════════════════════════════╝",
    ]

    # Animated title frames for starfield effect
    LOGO_ANIMATED_FRAMES = [
        [  # Frame 1
            "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "░░░ TERMINAL ARCADE ░░░",
            "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
        ],
        [  # Frame 2
            "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
            "▒▒▒ TERMINAL ARCADE ▒▒▒",
            "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
        ],
        [  # Frame 3
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
            "▓▓▓ TERMINAL ARCADE ▓▓▓",
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
        ],
    ]

    @staticmethod
    def draw_logo_large(renderer: Renderer, x: Optional[int] = None, y: Optional[int] = None,
                       color: str = Color.BRIGHT_CYAN):
        """Draw the large Terminal Arcade logo.

        Args:
            renderer: Renderer instance
            x, y: Top-left position (centered if None)
            color: Logo color
        """
        logo = Brand.LOGO_LARGE
        logo_width = max(len(line) for line in logo)
        logo_height = len(logo)

        if x is None:
            x = (renderer.width - logo_width) // 2
        if y is None:
            y = (renderer.height - logo_height) // 2

        for i, line in enumerate(logo):
            renderer.draw_text(x, y + i, line, color)

    @staticmethod
    def draw_logo_compact(renderer: Renderer, x: Optional[int] = None, y: Optional[int] = None,
                         color: str = Color.BRIGHT_YELLOW):
        """Draw the compact Terminal Arcade logo.

        Args:
            renderer: Renderer instance
            x, y: Top-left position (centered if None)
            color: Logo color
        """
        logo = Brand.LOGO_COMPACT
        logo_width = max(len(line) for line in logo)
        logo_height = len(logo)

        if x is None:
            x = (renderer.width - logo_width) // 2
        if y is None:
            y = (renderer.height - logo_height) // 2

        for i, line in enumerate(logo):
            renderer.draw_text(x, y + i, line, color)

    @staticmethod
    def draw_logo_cabinet(renderer: Renderer, x: Optional[int] = None, y: Optional[int] = None):
        """Draw the retro arcade cabinet logo with colors.

        Args:
            renderer: Renderer instance
            x, y: Top-left position (centered if None)
        """
        logo = Brand.LOGO_CABINET
        logo_width = max(len(line) for line in logo)
        logo_height = len(logo)

        if x is None:
            x = (renderer.width - logo_width) // 2
        if y is None:
            y = (renderer.height - logo_height) // 2

        colors = [
            Color.BRIGHT_YELLOW,  # Top border
            Color.BRIGHT_CYAN,    # Title
            Color.BRIGHT_YELLOW,  # Middle border
            Color.DARK_GRAY,      # Screen top
            Color.DARK_GRAY,      # Screen border
            Color.BRIGHT_GREEN,   # Press start
            Color.DARK_GRAY,      # Screen bottom
            Color.DARK_GRAY,      # Screen border
            Color.BRIGHT_MAGENTA, # Joysticks
            Color.BRIGHT_YELLOW,  # Bottom border
        ]

        for i, (line, color) in enumerate(zip(logo, colors)):
            renderer.draw_text(x, y + i, line, color)

    @staticmethod
    def draw_github_link(renderer: Renderer, x: Optional[int] = None, y: Optional[int] = None):
        """Draw GitHub attribution link.

        Args:
            renderer: Renderer instance
            x, y: Position (centered if None)
        """
        text = "github.com/jcaldwell-labs/terminal-arcade"

        if x is None:
            x = (renderer.width - len(text)) // 2
        if y is None:
            y = renderer.height - 3

        renderer.draw_text(x, y, text, Color.DARK_GRAY)

    @staticmethod
    def draw_credits(renderer: Renderer, x: Optional[int] = None, y: Optional[int] = None):
        """Draw developer credits.

        Args:
            renderer: Renderer instance
            x, y: Top-left position (centered if None)
        """
        credits = [
            "Created by jcaldwell-labs",
            "",
            "Built with Python, pygame, and blessed",
            "",
            "Licensed under MIT",
        ]

        max_width = max(len(line) for line in credits)

        if x is None:
            x = (renderer.width - max_width) // 2
        if y is None:
            y = (renderer.height - len(credits)) // 2

        for i, line in enumerate(credits):
            renderer.draw_text(x, y + i, line, Color.BRIGHT_WHITE)

    @staticmethod
    def draw_controls_help(renderer: Renderer, x: int = 2, y: Optional[int] = None):
        """Draw universal controls help.

        Args:
            renderer: Renderer instance
            x: Left margin
            y: Top position (bottom if None)
        """
        controls = [
            "CONTROLS: Arrow Keys/WASD = Move  |  Enter/Space = Select  |  ESC/Q = Back  |  X = Quit",
        ]

        if y is None:
            y = renderer.height - 2

        for i, line in enumerate(controls):
            renderer.draw_text(x, y + i, line, Color.DARK_GRAY)

    @staticmethod
    def get_section_header(section_name: str, icon: str = "◆") -> list:
        """Generate a decorative section header.

        Args:
            section_name: Name of the section (e.g., "ARCADE GAMES")
            icon: Icon character to use

        Returns:
            List of header lines
        """
        header_text = f"{icon} {section_name} {icon}"
        border = "═" * len(header_text)

        return [
            border,
            header_text,
            border,
        ]
