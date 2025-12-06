#!/usr/bin/env python3
"""Terminal Aspect Ratio Calibration Tool.

Interactive tool for calibrating terminal character aspect ratio.
Displays a test circle and allows adjustment to achieve proper proportions.

Usage:
    python -m atari_style.tools.aspect_calibration           # Interactive calibration
    python -m atari_style.tools.aspect_calibration --show    # Show current value
    python -m atari_style.tools.aspect_calibration --reset   # Reset to default
    python -m atari_style.tools.aspect_calibration --json    # JSON output

Examples:
    # Run interactive calibration mode
    python -m atari_style.tools.aspect_calibration

    # Display current aspect ratio setting
    python -m atari_style.tools.aspect_calibration --show

    # Reset to default value
    python -m atari_style.tools.aspect_calibration --reset

    # Machine-readable JSON output
    python -m atari_style.tools.aspect_calibration --show --json
"""

import argparse
import json
import math
import sys
import time
from typing import Tuple

from ..core.config import Config, DEFAULT_CHAR_ASPECT
from ..core.renderer import Renderer, Color


# Adjustment increment for aspect ratio
ASPECT_INCREMENT = 0.01


def draw_circle(
    renderer: Renderer,
    center_x: int,
    center_y: int,
    radius: int,
    char_aspect: float,
    color: str = Color.CYAN
) -> None:
    """Draw a circle adjusted for character aspect ratio.

    Args:
        renderer: Renderer instance to draw on
        center_x: X coordinate of circle center
        center_y: Y coordinate of circle center
        radius: Radius of the circle in characters
        char_aspect: Character aspect ratio (width/height)
        color: Color for the circle
    """
    # Draw circle by iterating angles
    for angle in range(360):
        rad = math.radians(angle)
        # X is stretched by 1/char_aspect to compensate for tall chars
        x = center_x + int(radius * math.cos(rad) / char_aspect)
        y = center_y + int(radius * math.sin(rad))
        renderer.set_pixel(x, y, '●', color)


def draw_crosshairs(
    renderer: Renderer,
    center_x: int,
    center_y: int,
    size: int,
    color: str = Color.GRAY
) -> None:
    """Draw crosshairs for reference.

    Args:
        renderer: Renderer instance to draw on
        center_x: X coordinate of center
        center_y: Y coordinate of center
        size: Length of crosshairs
        color: Color for crosshairs
    """
    # Horizontal line
    for x in range(center_x - size, center_x + size + 1):
        if x != center_x:
            renderer.set_pixel(x, center_y, '─', color)

    # Vertical line
    for y in range(center_y - size, center_y + size + 1):
        if y != center_y:
            renderer.set_pixel(center_x, y, '│', color)

    # Center point
    renderer.set_pixel(center_x, center_y, '┼', color)


def draw_instructions(
    renderer: Renderer,
    char_aspect: float,
    y_offset: int
) -> None:
    """Draw instruction text.

    Args:
        renderer: Renderer instance to draw on
        char_aspect: Current aspect ratio value
        y_offset: Y position to start drawing text
    """
    instructions = [
        f"Current aspect ratio: {char_aspect:.2f}",
        "",
        "Adjust until the circle appears round:",
        "  +/- or ↑/↓  : Adjust aspect ratio",
        "  ENTER       : Save and exit",
        "  ESC/Q       : Cancel without saving",
        "",
        "Hint: If circle is too tall, increase value",
        "      If circle is too wide, decrease value",
    ]

    for i, line in enumerate(instructions):
        renderer.draw_text(2, y_offset + i, line, Color.WHITE)


def run_interactive_calibration(
    verbose: bool = False,
    quiet: bool = False
) -> Tuple[bool, float]:
    """Run interactive calibration mode.

    Args:
        verbose: Enable verbose output
        quiet: Suppress non-essential output

    Returns:
        Tuple of (saved: bool, final_value: float)
    """
    config = Config.load()
    char_aspect = config.char_aspect
    renderer = Renderer()

    if verbose and not quiet:
        print(f"Starting calibration with aspect ratio: {char_aspect:.2f}",
              file=sys.stderr)

    saved = False

    try:
        renderer.enter_fullscreen()

        # Calculate display parameters
        center_x = renderer.width // 2
        center_y = renderer.height // 3
        radius = min(renderer.height // 4, 15)  # Reasonable circle size

        running = True
        while running:
            renderer.clear_buffer()

            # Draw calibration display
            draw_crosshairs(renderer, center_x, center_y, radius + 5)
            draw_circle(renderer, center_x, center_y, radius, char_aspect)
            draw_instructions(renderer, char_aspect, renderer.height - 12)

            renderer.render()

            # Get input using blessed's keyboard handling
            with renderer.term.cbreak():
                key = renderer.term.inkey(timeout=0.1)

                if key:
                    if key.name == 'KEY_UP' or key == '+' or key == '=':
                        char_aspect = min(1.0, char_aspect + ASPECT_INCREMENT)
                    elif key.name == 'KEY_DOWN' or key == '-' or key == '_':
                        char_aspect = max(0.1, char_aspect - ASPECT_INCREMENT)
                    elif key.name == 'KEY_ENTER':
                        # Save configuration
                        config.char_aspect = char_aspect
                        config.save()
                        saved = True
                        running = False
                    elif key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                        # Cancel without saving
                        running = False

    except KeyboardInterrupt:
        pass  # Clean exit on Ctrl+C
    finally:
        renderer.exit_fullscreen()

    return saved, char_aspect


def show_current_value(json_output: bool = False, quiet: bool = False) -> int:
    """Display current aspect ratio value.

    Args:
        json_output: Output as JSON
        quiet: Suppress non-essential output

    Returns:
        Exit code (0 for success)
    """
    config = Config.load()

    if json_output:
        result = {
            'char_aspect': config.char_aspect,
            'default': DEFAULT_CHAR_ASPECT,
            'config_file': str(Config.__dataclass_fields__)
        }
        print(json.dumps({'char_aspect': config.char_aspect,
                         'default': DEFAULT_CHAR_ASPECT}, indent=2))
    else:
        print(f"Current aspect ratio: {config.char_aspect:.2f}")
        if not quiet:
            print(f"Default value: {DEFAULT_CHAR_ASPECT:.2f}", file=sys.stderr)

    return 0


def reset_to_default(json_output: bool = False, quiet: bool = False) -> int:
    """Reset aspect ratio to default value.

    Args:
        json_output: Output as JSON
        quiet: Suppress non-essential output

    Returns:
        Exit code (0 for success)
    """
    config = Config.load()
    config.char_aspect = DEFAULT_CHAR_ASPECT
    config.save()

    if json_output:
        print(json.dumps({'char_aspect': config.char_aspect,
                         'reset': True}, indent=2))
    else:
        print(f"Reset aspect ratio to default: {DEFAULT_CHAR_ASPECT:.2f}")

    return 0


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog='aspect-calibration',
        description='Terminal aspect ratio calibration tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                  # Interactive calibration mode
  %(prog)s --show           # Display current value
  %(prog)s --reset          # Reset to default
  %(prog)s --show --json    # JSON output
        """
    )

    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        '--show',
        action='store_true',
        help='Show current aspect ratio value'
    )
    action_group.add_argument(
        '--reset',
        action='store_true',
        help='Reset aspect ratio to default'
    )

    # Output format
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    # Verbosity (mutually exclusive)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    verbosity_group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-essential output'
    )

    args = parser.parse_args()

    try:
        if args.show:
            return show_current_value(args.json, args.quiet)
        elif args.reset:
            return reset_to_default(args.json, args.quiet)
        else:
            # Interactive calibration mode
            saved, final_value = run_interactive_calibration(
                args.verbose, args.quiet
            )

            if args.json:
                print(json.dumps({
                    'char_aspect': final_value,
                    'saved': saved
                }, indent=2))
            elif not args.quiet:
                if saved:
                    print(f"Saved aspect ratio: {final_value:.2f}",
                          file=sys.stderr)
                else:
                    print("Calibration cancelled", file=sys.stderr)

            return 0 if saved else 1

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
