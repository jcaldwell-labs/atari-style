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
from .demos.flux_control import run_flux_control
from .demos.flux_control_patterns import run_pattern_flux
from .demos.flux_control_rhythm import run_rhythm_flux
from .demos.flux_control_zen import run_flux_zen
from .demos.flux_control_explorer import run_flux_explorer


def main():
    """Main entry point."""
    # Create menu items
    menu_items = [
        MenuItem("Pac-Man", run_pacman),
        MenuItem("Galaga", run_galaga),
        MenuItem("Grand Prix", run_grandprix),
        MenuItem("Breakout", run_breakout),
        MenuItem("Flux Control", run_flux_control),
        MenuItem("Flux Control: Patterns", run_pattern_flux),
        MenuItem("Flux Control: Rhythm", run_rhythm_flux),
        MenuItem("Flux Control: Zen", run_flux_zen),
        MenuItem("Flux Control: Explorer", run_flux_explorer),
        MenuItem("ASCII Painter", run_ascii_painter),
        MenuItem("Starfield", run_starfield),
        MenuItem("Screen Saver", run_screensaver),
        MenuItem("Platonic Solids", run_platonic_solids),
        MenuItem("Joystick Test", run_joystick_test),
        MenuItem("Exit", sys.exit),
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
