"""Zone mode runner for embedding atari-style demos in zones.

This module provides a headless mode for running parametric animations
that outputs ANSI frames to stdout for capture by parent processes.

Usage:
    python -m atari_style.zone_mode plasma --width 80 --height 24
    python -m atari_style.zone_mode lissajous --width 60 --height 20 --fps 10
"""

import argparse
import time
import sys
from .core.zone_renderer import ZoneRenderer
from .demos.visualizers.screensaver import (
    LissajousCurve,
    SpiralAnimation,
    CircleWaveAnimation,
    PlasmaAnimation,
)


# Available animations
ANIMATIONS = {
    'plasma': PlasmaAnimation,
    'lissajous': LissajousCurve,
    'spiral': SpiralAnimation,
    'waves': CircleWaveAnimation,
}


def run_zone_animation(animation_name: str, width: int = 80, height: int = 24, fps: int = 20):
    """Run an animation in zone mode.

    Args:
        animation_name: Name of the animation to run
        width: Zone width in characters
        height: Zone height in characters
        fps: Frames per second
    """
    if animation_name not in ANIMATIONS:
        print(f"Error: Unknown animation '{animation_name}'", file=sys.stderr)
        print(f"Available: {', '.join(ANIMATIONS.keys())}", file=sys.stderr)
        sys.exit(1)

    # Create renderer and animation
    renderer = ZoneRenderer(width=width, height=height)
    animation_class = ANIMATIONS[animation_name]
    animation = animation_class(renderer)

    # Animation loop
    frame_time = 1.0 / fps
    t = 0.0

    try:
        while True:
            start = time.time()

            # Clear and draw
            renderer.clear_buffer()
            animation.draw(t)
            renderer.render()

            # Update time
            t += frame_time

            # Sleep to maintain frame rate
            elapsed = time.time() - start
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        # Parent process closed pipe - normal exit
        pass


def main():
    """Main entry point for zone mode."""
    # Fix Windows encoding for Unicode characters (block chars, box drawing, etc.)
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='Run atari-style animations in zone mode for embedding'
    )
    parser.add_argument(
        'animation',
        choices=list(ANIMATIONS.keys()),
        help='Animation to run'
    )
    parser.add_argument(
        '--width',
        type=int,
        default=80,
        help='Zone width in characters (default: 80)'
    )
    parser.add_argument(
        '--height',
        type=int,
        default=24,
        help='Zone height in characters (default: 24)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=20,
        help='Frames per second (default: 20)'
    )

    args = parser.parse_args()

    run_zone_animation(
        args.animation,
        width=args.width,
        height=args.height,
        fps=args.fps
    )


if __name__ == '__main__':
    main()
