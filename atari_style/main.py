"""Main entry point for Atari-style terminal demos."""

import sys
from .core.menu import Menu, MenuItem
from .demos.starfield import run_starfield
from .demos.screensaver import run_screensaver
from .demos.joystick_test import run_joystick_test


def main():
    """Main entry point."""
    # Create menu items
    menu_items = [
        MenuItem(
            "Starfield Demo",
            run_starfield,
            "Fly through space with joystick-controlled speed and effects"
        ),
        MenuItem(
            "Screen Saver",
            run_screensaver,
            "Parametric animations: Lissajous, Spirals, Waves, and Plasma"
        ),
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
