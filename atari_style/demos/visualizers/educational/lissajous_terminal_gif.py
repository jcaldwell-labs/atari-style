#!/usr/bin/env python3
"""Lissajous Terminal GIF renderer - captures the classic light-brite dancing effect.

Renders the pure ASCII Lissajous curves at native terminal resolution for
authentic retro aesthetics - the original VHS-capture style from:
https://www.youtube.com/watch?v=ROBHjKZg5IY

Usage:
    python -m atari_style.demos.lissajous_terminal_gif --sweep circle_to_trefoil -o lissajous.gif
    python -m atari_style.demos.lissajous_terminal_gif --explore -o explore.gif
"""

import os
import math
import subprocess
import tempfile
import shutil
import platform
from typing import Tuple, List, Generator
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont


# Terminal color palette (Dracula-inspired)
COLOR_RGB = {
    'red': (255, 85, 85),
    'green': (80, 250, 123),
    'yellow': (241, 250, 140),
    'blue': (98, 114, 164),
    'magenta': (255, 121, 198),
    'cyan': (139, 233, 253),
    'white': (248, 248, 242),
    'bright_red': (255, 110, 110),
    'bright_green': (105, 255, 148),
    'bright_yellow': (255, 255, 165),
    'bright_blue': (189, 147, 249),
    'bright_magenta': (255, 146, 218),
    'bright_cyan': (164, 255, 255),
    'bright_white': (255, 255, 255),
}

# Rainbow palette for Lissajous
RAINBOW = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']

# Theme palettes
THEMES = {
    'rainbow': ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta'],
    'desert': ['bright_yellow', 'yellow', 'red', 'bright_red', 'magenta', 'white'],
    'ocean': ['blue', 'cyan', 'bright_cyan', 'green', 'bright_blue', 'white'],
    'forest': ['green', 'bright_green', 'yellow', 'cyan', 'blue', 'white'],
    'mountain': ['white', 'bright_cyan', 'cyan', 'blue', 'magenta', 'bright_blue'],
}


@dataclass
class CriticalPattern:
    """A stable Lissajous pattern at specific parameter ratios."""
    name: str
    a: float  # x frequency
    b: float  # y frequency
    delta: float  # phase offset (radians)


PATTERNS = {
    'circle': CriticalPattern("Circle", 1.0, 1.0, math.pi/2),
    'ellipse': CriticalPattern("Ellipse", 1.0, 1.0, math.pi/4),
    'figure8': CriticalPattern("Figure-8", 1.0, 2.0, 0),
    'bowtie': CriticalPattern("Bow-tie", 1.0, 2.0, math.pi/2),
    'trefoil': CriticalPattern("Trefoil", 2.0, 3.0, 0),
    'fish': CriticalPattern("Fish", 2.0, 3.0, math.pi/2),
    'quatrefoil': CriticalPattern("Quatrefoil", 3.0, 4.0, 0),
    'star5': CriticalPattern("Star-5", 2.0, 5.0, 0),
    'pentagram': CriticalPattern("Pentagram", 3.0, 5.0, 0),
}


def find_monospace_font(size: int):
    """Find a suitable monospace font."""
    paths = []
    if platform.system() == 'Windows':
        paths = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
            "C:/Windows/Fonts/lucon.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        ]

    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()


class TerminalCanvas:
    """Renders ASCII art to PIL images at terminal-native resolution."""

    def __init__(self, cols: int = 133, rows: int = 37, cell_width: int = 10, cell_height: int = 18):
        """Initialize terminal canvas.

        Args:
            cols: Terminal columns (character width)
            rows: Terminal rows (character height)
            cell_width: Pixel width per character cell
            cell_height: Pixel height per character cell
        """
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height

        # Image dimensions
        self.img_width = cols * cell_width
        self.img_height = rows * cell_height

        # Character buffer
        self.buffer = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.color_buffer = [['white' for _ in range(cols)] for _ in range(rows)]

        # Background color (dark terminal)
        self.bg_color = (30, 32, 44)

        # Font
        self.font = find_monospace_font(cell_height - 2)

    def clear(self):
        """Clear the buffer."""
        for y in range(self.rows):
            for x in range(self.cols):
                self.buffer[y][x] = ' '
                self.color_buffer[y][x] = 'white'

    def set_pixel(self, x: int, y: int, char: str, color: str = 'white'):
        """Set a character at position (x, y)."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color

    def render(self) -> Image.Image:
        """Render buffer to PIL Image."""
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for y in range(self.rows):
            for x in range(self.cols):
                char = self.buffer[y][x]
                if char == ' ':
                    continue

                color_name = self.color_buffer[y][x]
                rgb = COLOR_RGB.get(color_name, (248, 248, 242))

                px = x * self.cell_width
                py = y * self.cell_height

                draw.text((px, py), char, font=self.font, fill=rgb)

        return img


def draw_lissajous(canvas: TerminalCanvas, t: float, a: float, b: float, delta: float,
                   points: int = 500, trail_length: int = 8, palette: list = None):
    """Draw a Lissajous curve with coloring and motion trails.

    Args:
        canvas: Terminal canvas to draw on
        t: Current time (for animation)
        a: X frequency
        b: Y frequency
        delta: Phase offset
        points: Number of points to draw
        trail_length: Number of trailing frames to show (creates motion blur effect)
        palette: Color palette to use (defaults to RAINBOW)
    """
    if palette is None:
        palette = RAINBOW

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale_x = canvas.cols // 3
    scale_y = canvas.rows // 3

    # Draw trails first (older = dimmer)
    trail_chars = ['●', '○', '◦', '·', '·', '.', '.', '.']

    for trail in range(trail_length - 1, -1, -1):
        trail_t = t - trail * 0.02  # Each trail step is slightly in the past
        alpha = 1.0 - (trail / trail_length)  # Fade factor

        for i in range(points):
            angle = (i / points) * 2 * math.pi

            x = math.sin(a * angle + trail_t)
            y = math.sin(b * angle + delta + trail_t * 0.5)

            screen_x = int(cx + x * scale_x * 1.5)
            screen_y = int(cy + y * scale_y * 0.8)

            # Only draw if not at current position (avoid overlap with bright head)
            if trail > 0:
                color_idx = int((i / points) * len(palette))
                color = palette[color_idx % len(palette)]

                # Use dimmer character for trails
                char_idx = min(trail, len(trail_chars) - 1)
                char = trail_chars[char_idx]

                canvas.set_pixel(screen_x, screen_y, char, color)

    # Draw the current (brightest) curve on top
    for i in range(points):
        angle = (i / points) * 2 * math.pi

        x = math.sin(a * angle + t)
        y = math.sin(b * angle + delta + t * 0.5)

        screen_x = int(cx + x * scale_x * 1.5)
        screen_y = int(cy + y * scale_y * 0.8)

        color_idx = int((i / points) * len(palette))
        color = palette[color_idx % len(palette)]

        canvas.set_pixel(screen_x, screen_y, '●', color)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in/out function."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation."""
    return start + (end - start) * t


def generate_sweep_frames(canvas: TerminalCanvas, start_pattern: str, end_pattern: str,
                          duration: float, fps: int) -> Generator[Image.Image, None, None]:
    """Generate frames sweeping between two Lissajous patterns.

    This creates the dancing/morphing effect as parameters transition.
    """
    p1 = PATTERNS[start_pattern]
    p2 = PATTERNS[end_pattern]

    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps  # Current time
        progress = frame / total_frames  # 0 to 1

        # Ease the transition for smoother morphing
        eased = ease_in_out_cubic(progress)

        # Interpolate parameters
        a = lerp(p1.a, p2.a, eased)
        b = lerp(p1.b, p2.b, eased)
        delta = lerp(p1.delta, p2.delta, eased)

        # Clear and draw
        canvas.clear()
        draw_lissajous(canvas, t * 2, a, b, delta)

        # Add parameter info overlay
        info = f"a={a:.2f} b={b:.2f} d={delta:.2f}"
        for i, char in enumerate(info):
            canvas.set_pixel(2 + i, 1, char, 'cyan')

        yield canvas.render()


def generate_exploration_frames(canvas: TerminalCanvas, duration: float, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate frames exploring parameter space with smooth transitions.

    This creates the wandering, dancing effect - moving through transition
    zones between stable patterns.
    """
    total_frames = int(duration * fps)

    # Define a path through interesting transition zones
    # These are the unstable regions between stable patterns where the curve dances
    waypoints = [
        (1.0, 1.0, math.pi/2),     # Circle
        (1.2, 1.8, math.pi/3),     # Transition to figure-8
        (1.0, 2.0, 0),             # Figure-8
        (1.5, 2.5, math.pi/4),     # Transition zone (dancing)
        (2.0, 3.0, 0),             # Trefoil
        (2.3, 3.5, math.pi/6),     # Transition (unstable dance)
        (2.5, 4.0, math.pi/8),     # Transition to quatrefoil
        (3.0, 4.0, 0),             # Quatrefoil
        (2.5, 4.5, math.pi/4),     # Complex transition
        (2.0, 5.0, 0),             # Star-5
        (2.5, 4.2, math.pi/3),     # Back through transition
        (1.8, 2.2, math.pi/5),     # More instability
        (1.0, 1.0, math.pi/2),     # Return to circle
    ]

    # Time to spend transitioning between waypoints
    frames_per_segment = total_frames // (len(waypoints) - 1)

    current_waypoint = 0

    for frame in range(total_frames):
        t = frame / fps

        # Determine which segment we're in
        segment = min(frame // frames_per_segment, len(waypoints) - 2)
        segment_progress = (frame % frames_per_segment) / frames_per_segment

        # Get start and end waypoints for this segment
        a1, b1, d1 = waypoints[segment]
        a2, b2, d2 = waypoints[segment + 1]

        # Smooth interpolation
        eased = ease_in_out_cubic(segment_progress)
        a = lerp(a1, a2, eased)
        b = lerp(b1, b2, eased)
        delta = lerp(d1, d2, eased)

        # Add subtle oscillation for extra "dancing" effect
        a += math.sin(t * 3) * 0.05
        b += math.cos(t * 2.7) * 0.05
        delta += math.sin(t * 1.5) * 0.1

        # Clear and draw
        canvas.clear()
        draw_lissajous(canvas, t * 1.5, a, b, delta, points=600)

        # Add info overlay
        info = f"{a:.1f}:{b:.1f}"
        for i, char in enumerate(info):
            canvas.set_pixel(canvas.cols - len(info) - 2 + i, 1, char, 'yellow')

        yield canvas.render()


def generate_stability_dance_frames(canvas: TerminalCanvas, pattern_name: str,
                                    duration: float, fps: int
                                    ) -> Generator[Image.Image, None, None]:
    """Generate frames showing a pattern dancing around a stable point.

    This shows the pattern oscillating near (but not quite at) the stable ratio,
    creating the characteristic "breathing" and "wobbling" effect.
    """
    pattern = PATTERNS[pattern_name]
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps

        # Oscillate around the stable point
        # The closer to the exact ratio, the more stable; further = more dancing
        wobble_amount = 0.15  # How far to wander from stable point

        # Multi-frequency wobble for complex motion
        a = pattern.a + math.sin(t * 1.2) * wobble_amount + math.sin(t * 2.5) * (wobble_amount * 0.3)
        b = pattern.b + math.cos(t * 0.9) * wobble_amount + math.cos(t * 3.1) * (wobble_amount * 0.3)
        delta = pattern.delta + math.sin(t * 0.7) * 0.3

        canvas.clear()
        draw_lissajous(canvas, t * 2, a, b, delta, points=500)

        # Label
        for i, char in enumerate(pattern.name):
            canvas.set_pixel(2 + i, 1, char, 'bright_cyan')

        yield canvas.render()


def generate_showcase_frames(canvas: TerminalCanvas, fps: int, theme: str = 'ocean'
                             ) -> Generator[Image.Image, None, None]:
    """Generate a showcase cycling through all patterns with fast, fun transitions.

    Quick pacing: ~1.5s per pattern hold, ~0.5s transitions
    Visits all 9 patterns with mesmerizing intermediate states.
    """
    palette = THEMES.get(theme, THEMES['ocean'])

    # All patterns in an interesting order (grouped by complexity)
    pattern_sequence = [
        'circle',      # Simple start
        'ellipse',     # Slight variation
        'figure8',     # First complex shape
        'bowtie',      # Figure8 variant
        'trefoil',     # Three lobes
        'fish',        # Trefoil variant
        'quatrefoil',  # Four lobes
        'star5',       # Five points
        'pentagram',   # Most complex
        'circle',      # Return to start (loop point)
    ]

    # Timing: fast but appreciable
    hold_time = 1.2        # Seconds to hold each stable pattern
    transition_time = 0.6  # Seconds for each transition (fast!)

    frame_num = 0

    for i in range(len(pattern_sequence) - 1):
        p1 = PATTERNS[pattern_sequence[i]]
        p2 = PATTERNS[pattern_sequence[i + 1]]

        # Hold on current pattern (with subtle dancing)
        hold_frames = int(hold_time * fps)
        for f in range(hold_frames):
            t = frame_num / fps

            # Subtle wobble during hold for visual interest
            wobble = 0.03
            a = p1.a + math.sin(t * 4) * wobble
            b = p1.b + math.cos(t * 3.5) * wobble
            delta = p1.delta + math.sin(t * 2) * 0.05

            canvas.clear()
            draw_lissajous(canvas, t * 2.5, a, b, delta, points=600, trail_length=6, palette=palette)

            # Pattern label
            label = p1.name
            for j, char in enumerate(label):
                canvas.set_pixel(2 + j, 1, char, 'bright_white')

            yield canvas.render()
            frame_num += 1

        # Fast transition to next pattern
        trans_frames = int(transition_time * fps)
        for f in range(trans_frames):
            t = frame_num / fps
            progress = f / trans_frames

            # Use smooth easing for pleasing motion
            eased = ease_in_out_cubic(progress)

            # Interpolate parameters
            a = lerp(p1.a, p2.a, eased)
            b = lerp(p1.b, p2.b, eased)
            delta = lerp(p1.delta, p2.delta, eased)

            # Add extra "pop" during transition - slight overshoot and bounce
            bounce = math.sin(progress * math.pi) * 0.1
            a += bounce
            b += bounce

            canvas.clear()
            draw_lissajous(canvas, t * 2.5, a, b, delta, points=600, trail_length=10, palette=palette)

            # Transition indicator
            arrow = f"{p1.name} -> {p2.name}"
            for j, char in enumerate(arrow):
                canvas.set_pixel(2 + j, 1, char, 'yellow')

            yield canvas.render()
            frame_num += 1


def render_gif(output_path: str, frames: Generator[Image.Image, None, None],
               fps: int = 15, total_frames: int = 0) -> bool:
    """Render frames to GIF using two-pass palette optimization."""

    # Find ffmpeg
    ffmpeg_cmd = 'ffmpeg'
    if platform.system() == 'Windows':
        scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
        if os.path.exists(scoop_ffmpeg):
            ffmpeg_cmd = scoop_ffmpeg

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix='lissajous_')

    print(f"Rendering frames to: {temp_dir}")

    try:
        # Save frames
        frame_count = 0
        for i, frame in enumerate(frames):
            frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
            frame.save(frame_path)
            frame_count += 1

            if (i + 1) % 30 == 0:
                print(f"  Frame {i + 1}...")

        print(f"Total frames: {frame_count}")
        print("Encoding GIF (two-pass palette)...")

        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')
        palette_path = os.path.join(temp_dir, 'palette.png')

        # Pass 1: Generate optimal palette
        palette_cmd = [
            ffmpeg_cmd, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-vf', 'palettegen=stats_mode=diff',
            palette_path
        ]

        result = subprocess.run(palette_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Palette generation failed: {result.stderr}")
            return False

        # Pass 2: Encode GIF with palette
        gif_cmd = [
            ffmpeg_cmd, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-i', palette_path,
            '-lavfi', 'paletteuse=dither=bayer:bayer_scale=5',
            output_path
        ]

        result = subprocess.run(gif_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"GIF encoding failed: {result.stderr}")
            return False

        size = os.path.getsize(output_path) / 1024
        print(f"Success! {output_path} ({size:.1f} KB)")
        return True

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Render Lissajous terminal GIFs - classic light-brite dancing effect"
    )

    parser.add_argument('-o', '--output', default='lissajous.gif',
                       help='Output GIF path')
    parser.add_argument('--cols', type=int, default=133,
                       help='Terminal columns (default: 133)')
    parser.add_argument('--rows', type=int, default=37,
                       help='Terminal rows (default: 37)')
    parser.add_argument('--duration', type=float, default=10,
                       help='Duration in seconds (default: 10)')
    parser.add_argument('--fps', type=int, default=15,
                       help='Frames per second (default: 15)')

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--sweep', nargs=2, metavar=('FROM', 'TO'),
                           help='Sweep between two patterns: ' + ', '.join(PATTERNS.keys()))
    mode_group.add_argument('--explore', action='store_true',
                           help='Explore parameter space with dancing transitions')
    mode_group.add_argument('--dance', metavar='PATTERN',
                           help='Dance around a stable pattern: ' + ', '.join(PATTERNS.keys()))
    mode_group.add_argument('--showcase', metavar='THEME',
                           help='Fast tour through ALL patterns with theme: desert, ocean, forest, mountain')

    args = parser.parse_args()

    # Create canvas at terminal-native resolution
    canvas = TerminalCanvas(cols=args.cols, rows=args.rows)

    print(f"Canvas: {canvas.cols}x{canvas.rows} chars = {canvas.img_width}x{canvas.img_height} pixels")

    # Generate frames based on mode
    if args.sweep:
        start, end = args.sweep
        if start not in PATTERNS or end not in PATTERNS:
            print(f"Unknown pattern. Available: {', '.join(PATTERNS.keys())}")
            return 1
        frames = generate_sweep_frames(canvas, start, end, args.duration, args.fps)

    elif args.explore:
        frames = generate_exploration_frames(canvas, args.duration, args.fps)

    elif args.dance:
        if args.dance not in PATTERNS:
            print(f"Unknown pattern. Available: {', '.join(PATTERNS.keys())}")
            return 1
        frames = generate_stability_dance_frames(canvas, args.dance, args.duration, args.fps)

    elif args.showcase:
        if args.showcase not in THEMES:
            print(f"Unknown theme. Available: {', '.join(THEMES.keys())}")
            return 1
        frames = generate_showcase_frames(canvas, args.fps, args.showcase)

    # Render to GIF
    success = render_gif(args.output, frames, args.fps)
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
