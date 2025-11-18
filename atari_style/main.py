"""Main entry point for Atari-style terminal demos."""

import sys
from .core.menu import Menu, MenuItem
from .demos.starfield import run_starfield
from .demos.screensaver import run_screensaver
from .demos.joystick_test import run_joystick_test
from .demos.breakout import run_breakout
from .demos.pacman import run_pacman
from .demos.galaga import run_galaga
from .demos.grandprix import run_grandprix
from .demos.ascii_painter import run_ascii_painter
from .demos.platonic_solids import run_platonic_solids


def main():
    """Main entry point."""
    # Create menu items
    menu_items = [
        # Games
        MenuItem(
            "Pac-Man",
            run_pacman,
            "Classic maze chase game with ghost AI and power-ups"
        ),
        MenuItem(
            "Galaga",
            run_galaga,
            "Space shooter with wave-based enemies and dive attacks"
        ),
        MenuItem(
            "Grand Prix",
            run_grandprix,
            "First-person 3D racing with curves, hills, and opponents"
        ),
        MenuItem(
            "Breakout",
            run_breakout,
            "Paddle game with power-ups, multiple brick types, and combos"
        ),

        # Creative Tools
        MenuItem(
            "ASCII Painter",
            run_ascii_painter,
            "Joystick-controlled ASCII art editor with tools and palettes"
        ),

        # Demos
        MenuItem(
            "Starfield",
            run_starfield,
            "Fly through space with joystick-controlled speed and effects"
        ),
        MenuItem(
            "Screen Saver",
            run_screensaver,
            "8 parametric animations with real-time parameter control"
        ),
        MenuItem(
            "Platonic Solids",
            run_platonic_solids,
            "Interactive 3D viewer for the five Platonic solids"
        ),

        # Utilities
        MenuItem(
            "Joystick Test",
            run_joystick_test,
            "Verify joystick connection and test all axes and buttons"
        ),
        MenuItem(
            "Exit",
            sys.exit,
            "Exit the application"
        ),
    ]

    # Create and run menu
    menu = Menu("ATARI-STYLE TERMINAL DEMOS", menu_items)

    try:
        menu.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("\nThanks for playing!")


if __name__ == "__main__":
    main()
