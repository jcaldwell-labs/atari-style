"""Flux Ultimate Demo - Color journey through all visual modes.

VHS-compatible: Uses single fullscreen session and 20 FPS frame rate.
"""

import time
from ..core.renderer import Renderer, Color
from .flux_control_zen import FluidLattice
from .flux_showcase import (
    FluxShowcase, OCEAN, FIRE, RAINBOW, SUNSET, DESERT,
    CHARS_WAVE, CHARS_DENSE, CHARS_DOTS
)

# VHS-compatible frame rate (20 FPS = 0.05s sleep)
FRAME_DELAY = 0.05


def run_ultimate_showcase(total_duration: int = 240):
    """Run the ultimate color journey showcase.

    VHS-compatible: Single while loop with time-based mode switching.
    Uses same pattern as proven run_flux_showcase().

    Segments:
    1. Ocean (40s) - Deep blue calm opening
    2. Fire (35s) - Warm energy burst
    3. Rainbow (40s) - Peak visual excitement
    4. Sunset (35s) - Golden hour warmth
    5. Desert (30s) - Sandy dune tones
    6. Heat (35s) - Energy visualization
    7. Ocean (25s) - Calm outro (full circle)
    """
    # Segments with cumulative time boundaries
    segments = [
        (0, 'ocean', CHARS_WAVE, 0.3),      # 0-40s: Calm opening
        (40, 'fire', CHARS_DENSE, 0.5),     # 40-75s: Energy burst
        (75, 'rainbow', CHARS_WAVE, 0.8),   # 75-115s: Peak excitement
        (115, 'sunset', CHARS_DOTS, 0.4),   # 115-150s: Golden warmth
        (150, 'desert', CHARS_DENSE, 0.3),  # 150-180s: Sandy dunes
        (180, 'heat', CHARS_DENSE, 0.5),    # 180-215s: Energy heat
        (215, 'ocean', CHARS_WAVE, 0.2),    # 215-240s: Calm outro
    ]

    # Create single showcase instance for entire run
    showcase = FluxShowcase()
    showcase.renderer.enter_fullscreen()

    try:
        start_time = time.time()
        last_time = start_time
        current_segment = -1

        # Single while loop - proven VHS-compatible pattern
        while time.time() - start_time < total_duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time

            # Find current segment based on elapsed time
            new_segment = 0
            for i, (boundary, _, _, _) in enumerate(segments):
                if elapsed >= boundary:
                    new_segment = i

            # Switch mode if segment changed
            if new_segment != current_segment:
                current_segment = new_segment
                _, mode, chars, speed = segments[current_segment]
                showcase.color_mode = mode
                showcase.char_set = chars
                showcase.color_speed = speed

            showcase.update(dt)
            showcase.draw(show_ui=False)
            time.sleep(FRAME_DELAY)
    finally:
        showcase.renderer.exit_fullscreen()


def run_quick_sampler(duration: int = 120):
    """Quick 2-minute sampler of all modes.

    VHS-compatible: Single while loop with time-based mode switching.
    Great for YouTube shorts - 20 seconds per mode.
    """
    # Segments with cumulative time boundaries (20s each)
    segments = [
        (0, 'ocean', CHARS_WAVE, 0.4),      # 0-20s
        (20, 'fire', CHARS_DENSE, 0.6),     # 20-40s
        (40, 'rainbow', CHARS_WAVE, 0.9),   # 40-60s
        (60, 'sunset', CHARS_DOTS, 0.4),    # 60-80s
        (80, 'desert', CHARS_DENSE, 0.3),   # 80-100s
        (100, 'ocean', CHARS_WAVE, 0.3),    # 100-120s
    ]

    showcase = FluxShowcase()
    showcase.renderer.enter_fullscreen()

    try:
        start_time = time.time()
        last_time = start_time
        current_segment = -1

        # Single while loop - proven VHS-compatible pattern
        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time

            # Find current segment based on elapsed time
            new_segment = 0
            for i, (boundary, _, _, _) in enumerate(segments):
                if elapsed >= boundary:
                    new_segment = i

            # Switch mode if segment changed
            if new_segment != current_segment:
                current_segment = new_segment
                _, mode, chars, speed = segments[current_segment]
                showcase.color_mode = mode
                showcase.char_set = chars
                showcase.color_speed = speed

            showcase.update(dt)
            showcase.draw(show_ui=False)
            time.sleep(FRAME_DELAY)
    finally:
        showcase.renderer.exit_fullscreen()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        run_quick_sampler()
    else:
        run_ultimate_showcase()
