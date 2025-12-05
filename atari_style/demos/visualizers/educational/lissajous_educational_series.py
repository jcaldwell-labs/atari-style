#!/usr/bin/env python3
"""Lissajous Educational Series - Complete 5-Part Video Course.

Renders educational video segments explaining Lissajous curve mathematics:
- Part I: Introduction - What are Lissajous curves?
- Part II: Pattern Gallery - Classic shapes and their ratios
- Part III: Phase and Frequency Exploration
- Part IV: Real-World Applications
- Part V: Complete Game Demo

Usage:
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 1 -o intro.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 2 -o gallery.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 3 -o phase.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 4 -o applications.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 5 -o game.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --full-series -o full_series.gif

Preview mode (fast iteration):
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 1 --preview
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 2 --preview --start 10 --end 20
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --full-series --preview --duration 10
"""

import math
from dataclasses import dataclass
from typing import Generator, List, Optional

from PIL import Image

from .lissajous_terminal_gif import (
    TerminalCanvas, draw_lissajous, render_gif,
    ease_in_out_cubic, lerp, THEMES
)


# =============================================================================
# EDUCATIONAL CONSTANTS
# =============================================================================

# Frequency ratios with their visual characteristics
FREQUENCY_RATIOS = [
    ("1:1", 1.0, 1.0, "Circle/Ellipse - same frequency"),
    ("1:2", 1.0, 2.0, "Figure-8 - octave relationship"),
    ("2:3", 2.0, 3.0, "Trefoil - perfect fifth"),
    ("3:4", 3.0, 4.0, "Quatrefoil - perfect fourth"),
    ("1:3", 1.0, 3.0, "Three loops - octave + fifth"),
    ("2:5", 2.0, 5.0, "Star-5 - complex harmony"),
    ("3:5", 3.0, 5.0, "Pentagram - major sixth"),
]

# Phase demonstrations
PHASE_STEPS = [
    (0, "δ=0: Open curve"),
    (math.pi / 6, "δ=π/6: Slight tilt"),
    (math.pi / 4, "δ=π/4: 45° rotation"),
    (math.pi / 3, "δ=π/3: 60° rotation"),
    (math.pi / 2, "δ=π/2: Closed loop"),
    (2 * math.pi / 3, "δ=2π/3: Reversing"),
    (math.pi, "δ=π: Mirrored open"),
]

# Application examples
APPLICATIONS = [
    ("Oscilloscope", "XY mode displays phase relationships"),
    ("Laser Shows", "Galvanometers trace Lissajous patterns"),
    ("Audio Sync", "Frequency ratios = musical intervals"),
    ("Harmonograph", "Mechanical pendulum drawing"),
    ("Sonar/Radar", "Signal phase comparison"),
]


# =============================================================================
# TITLE CARD RENDERER
# =============================================================================

def draw_title_card(canvas: TerminalCanvas, title: str, subtitle: str = "",
                    color: str = 'bright_cyan'):
    """Draw a centered title card."""
    # Center the title
    title_x = (canvas.cols - len(title)) // 2
    title_y = canvas.rows // 2 - 2

    # Draw title
    for i, char in enumerate(title):
        canvas.set_pixel(title_x + i, title_y, char, color)

    # Draw subtitle if provided
    if subtitle:
        sub_x = (canvas.cols - len(subtitle)) // 2
        sub_y = title_y + 2
        for i, char in enumerate(subtitle):
            canvas.set_pixel(sub_x + i, sub_y, char, 'white')

    # Draw decorative line
    line_y = title_y + 4
    line_width = max(len(title), len(subtitle)) + 10
    line_x = (canvas.cols - line_width) // 2
    for i in range(line_width):
        char = '═' if i == 0 or i == line_width - 1 else '─'
        canvas.set_pixel(line_x + i, line_y, char, 'cyan')


def draw_info_overlay(canvas: TerminalCanvas, lines: List[str], x: int = 2, y: int = 1,
                      color: str = 'yellow'):
    """Draw info text overlay."""
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            canvas.set_pixel(x + j, y + i, char, color)


def draw_equation(canvas: TerminalCanvas, y: int):
    """Draw the Lissajous parametric equations."""
    eq1 = "x = sin(a·t + δ)"
    eq2 = "y = sin(b·t)"

    x1 = (canvas.cols - len(eq1)) // 2
    x2 = (canvas.cols - len(eq2)) // 2

    for i, char in enumerate(eq1):
        canvas.set_pixel(x1 + i, y, char, 'bright_green')
    for i, char in enumerate(eq2):
        canvas.set_pixel(x2 + i, y + 1, char, 'bright_green')


# =============================================================================
# PART I: INTRODUCTION - What are Lissajous Curves?
# =============================================================================

def generate_part1_intro_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate title frames for Part I."""
    duration = 3.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        canvas.clear()
        alpha = min(1.0, frame / (fps * 0.5))

        if alpha > 0.3:
            draw_title_card(canvas, "PART I", "Introduction to Lissajous Curves")

        yield canvas.render()


def generate_what_is_lissajous_frames(canvas: TerminalCanvas, fps: int
                                      ) -> Generator[Image.Image, None, None]:
    """Generate frames explaining what Lissajous curves are."""
    duration = 6.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Draw a simple Lissajous curve building up
        progress = min(1.0, frame / (total_frames * 0.7))
        cx = canvas.cols // 2
        cy = canvas.rows // 2
        scale_x = canvas.cols // 4
        scale_y = canvas.rows // 4

        # Draw partial curve based on progress
        points = int(400 * progress)
        for i in range(points):
            angle = (i / 400) * 2 * math.pi
            px = math.sin(1 * angle + t)
            py = math.sin(2 * angle + math.pi / 2)

            screen_x = int(cx + px * scale_x * 1.2)
            screen_y = int(cy + py * scale_y * 0.7)

            if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                color = 'bright_cyan' if i > points - 20 else 'cyan'
                canvas.set_pixel(screen_x, screen_y, '●', color)

        # Explanation text
        info = [
            "LISSAJOUS CURVES",
            "─" * 18,
            "",
            "Named after Jules",
            "Antoine Lissajous",
            "(1822-1880)",
            "",
            "Curves formed by",
            "combining two",
            "perpendicular",
            "oscillations.",
        ]
        draw_info_overlay(canvas, info, x=2, y=2)

        yield canvas.render()


def generate_equation_explanation_frames(canvas: TerminalCanvas, fps: int
                                         ) -> Generator[Image.Image, None, None]:
    """Generate frames explaining the parametric equations."""
    duration = 8.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Draw the curve
        cx = canvas.cols // 2 + 15
        cy = canvas.rows // 2
        scale_x = canvas.cols // 5
        scale_y = canvas.rows // 4

        # Animate through parameter t
        anim_t = t * 0.5
        for i in range(300):
            angle = (i / 300) * 2 * math.pi
            px = math.sin(2 * angle + anim_t)
            py = math.sin(3 * angle + anim_t * 0.3)

            screen_x = int(cx + px * scale_x)
            screen_y = int(cy + py * scale_y * 0.6)

            if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                # Color by angle
                colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']
                color = colors[int((i / 300) * len(colors)) % len(colors)]
                canvas.set_pixel(screen_x, screen_y, '●', color)

        # Equations on left side
        eq_x = 3
        eq_y = 4

        lines = [
            "THE EQUATIONS",
            "─" * 15,
            "",
            "x = sin(a·t + δ)",
            "y = sin(b·t)",
            "",
            "Where:",
            "  a = x frequency",
            "  b = y frequency",
            "  δ = phase offset",
            "  t = time (0 to 2π)",
            "",
            "The ratio a:b",
            "determines the",
            "pattern shape!",
        ]

        for i, line in enumerate(lines):
            color = 'bright_green' if 'sin' in line else 'white'
            if line.startswith('─'):
                color = 'cyan'
            draw_info_overlay(canvas, [line], x=eq_x, y=eq_y + i, color=color)

        yield canvas.render()


def generate_xy_visualization_frames(canvas: TerminalCanvas, fps: int
                                     ) -> Generator[Image.Image, None, None]:
    """Generate L-shaped visualization showing X and Y components."""
    duration = 10.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Layout: X oscillator on top, Y oscillator on left, curve in center
        margin = 8
        curve_cx = canvas.cols // 2 + 10
        curve_cy = canvas.rows // 2 + 3
        curve_scale_x = 20
        curve_scale_y = 8

        # Parameters
        a, b = 2.0, 3.0
        delta = math.pi / 4
        anim_phase = t * 2

        # Current point on curve
        current_x = math.sin(a * anim_phase + delta)
        current_y = math.sin(b * anim_phase)

        # Draw X oscillator (horizontal bar at top)
        x_bar_y = margin
        x_bar_left = curve_cx - curve_scale_x - 5
        x_bar_right = curve_cx + curve_scale_x + 5
        for x in range(x_bar_left, x_bar_right + 1):
            canvas.set_pixel(x, x_bar_y, '─', 'blue')
        # X marker
        x_marker = int(curve_cx + current_x * curve_scale_x)
        canvas.set_pixel(x_marker, x_bar_y, '●', 'bright_green')
        canvas.set_pixel(x_marker, x_bar_y - 1, '▼', 'bright_green')

        # Draw Y oscillator (vertical bar on left)
        y_bar_x = margin
        y_bar_top = curve_cy - curve_scale_y - 2
        y_bar_bottom = curve_cy + curve_scale_y + 2
        for y in range(y_bar_top, y_bar_bottom + 1):
            canvas.set_pixel(y_bar_x, y, '│', 'blue')
        # Y marker
        y_marker = int(curve_cy + current_y * curve_scale_y * 0.8)
        canvas.set_pixel(y_bar_x, y_marker, '●', 'bright_yellow')
        canvas.set_pixel(y_bar_x + 1, y_marker, '▶', 'bright_yellow')

        # Draw projection lines (dashed)
        # Vertical line from X marker
        for y in range(x_bar_y + 1, int(curve_cy + current_y * curve_scale_y * 0.8)):
            if y % 2 == 0:
                canvas.set_pixel(x_marker, y, '┊', 'green')
        # Horizontal line from Y marker
        for x in range(y_bar_x + 2, x_marker):
            if x % 2 == 0:
                canvas.set_pixel(x, y_marker, '┄', 'yellow')

        # Draw the Lissajous curve
        for i in range(300):
            angle = (i / 300) * 2 * math.pi
            px = math.sin(a * angle + delta)
            py = math.sin(b * angle)

            screen_x = int(curve_cx + px * curve_scale_x)
            screen_y = int(curve_cy + py * curve_scale_y * 0.8)

            if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                canvas.set_pixel(screen_x, screen_y, '·', 'cyan')

        # Draw current point (bright)
        point_x = int(curve_cx + current_x * curve_scale_x)
        point_y = int(curve_cy + current_y * curve_scale_y * 0.8)
        canvas.set_pixel(point_x, point_y, '●', 'bright_white')

        # Labels
        draw_info_overlay(canvas, ["X = sin(2t + π/4)"], x=x_bar_left, y=x_bar_y - 2, color='green')
        draw_info_overlay(canvas, ["Y"], x=margin - 1, y=y_bar_top - 1, color='yellow')
        draw_info_overlay(canvas, ["="], x=margin - 1, y=y_bar_top, color='yellow')
        draw_info_overlay(canvas, ["sin(3t)"], x=margin + 2, y=y_bar_top, color='yellow')

        # Info box
        info = [
            "L-SHAPED VIEW",
            "─" * 14,
            "X and Y oscillate",
            "independently.",
            "",
            "The curve traces",
            "their combined",
            "motion over time.",
        ]
        draw_info_overlay(canvas, info, x=canvas.cols - 20, y=2, color='white')

        yield canvas.render()


def generate_part1_frames(canvas: TerminalCanvas, fps: int
                          ) -> Generator[Image.Image, None, None]:
    """Generate all Part I frames."""
    yield from generate_part1_intro_frames(canvas, fps)
    yield from generate_what_is_lissajous_frames(canvas, fps)
    yield from generate_equation_explanation_frames(canvas, fps)
    yield from generate_xy_visualization_frames(canvas, fps)


# =============================================================================
# PART II: PATTERN GALLERY - Classic Shapes
# =============================================================================

# Gallery patterns with educational descriptions
GALLERY_PATTERNS = [
    ("Circle", 1.0, 1.0, math.pi / 2, "The simplest case: a=b with 90° phase"),
    ("Figure-8", 1.0, 2.0, 0, "Ratio 1:2 creates the infinity symbol"),
    ("Trefoil", 2.0, 3.0, 0, "Ratio 2:3 - three interlocking loops"),
    ("Quatrefoil", 3.0, 4.0, 0, "Ratio 3:4 - four-petaled flower"),
    ("Star-5", 2.0, 5.0, 0, "Ratio 2:5 - five-pointed star"),
    ("Pentagram", 3.0, 5.0, 0, "Ratio 3:5 - complex interlaced star"),
]


def generate_part2_intro_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate title frames for Part II."""
    duration = 3.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        canvas.clear()
        alpha = min(1.0, frame / (fps * 0.5))

        if alpha > 0.3:
            draw_title_card(canvas, "PART II", "The Pattern Gallery")

        yield canvas.render()


def generate_pattern_showcase_frames(canvas: TerminalCanvas, fps: int
                                     ) -> Generator[Image.Image, None, None]:
    """Generate frames showcasing each classic pattern."""
    time_per_pattern = 4.0

    for name, a, b, delta, description in GALLERY_PATTERNS:
        frames = int(time_per_pattern * fps)

        for frame in range(frames):
            t = frame / fps
            canvas.clear()

            # Draw the pattern large and centered
            cx = canvas.cols // 2
            cy = canvas.rows // 2
            scale_x = canvas.cols // 3
            scale_y = canvas.rows // 3

            # Animate the curve
            for i in range(500):
                angle = (i / 500) * 2 * math.pi
                px = math.sin(a * angle + t * 1.5 + delta)
                py = math.sin(b * angle + t * 0.5)

                screen_x = int(cx + px * scale_x * 1.2)
                screen_y = int(cy + py * scale_y * 0.7)

                if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                    # Rainbow coloring
                    colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']
                    color = colors[int((i / 500) * len(colors)) % len(colors)]
                    canvas.set_pixel(screen_x, screen_y, '●', color)

            # Pattern info box
            ratio = f"{int(a)}:{int(b)}"
            info = [
                f"═══ {name} ═══",
                "",
                f"Ratio: {ratio}",
                f"Phase: {'π/2' if delta == math.pi/2 else '0'}",
                "",
                "─" * 25,
                description[:25] if len(description) <= 25 else description[:22] + "...",
            ]
            draw_info_overlay(canvas, info, x=2, y=2, color='bright_white')

            yield canvas.render()


def generate_ratio_comparison_frames(canvas: TerminalCanvas, fps: int
                                     ) -> Generator[Image.Image, None, None]:
    """Generate frames comparing multiple patterns side by side."""
    duration = 8.0
    total_frames = int(duration * fps)

    # Show 3 patterns at once for comparison
    patterns = GALLERY_PATTERNS[:3]  # Circle, Figure-8, Trefoil

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Title
        title = "RATIO COMPARISON"
        title_x = (canvas.cols - len(title)) // 2
        draw_info_overlay(canvas, [title, "═" * len(title)], x=title_x, y=1, color='bright_cyan')

        # Draw 3 patterns side by side
        section_width = canvas.cols // 3
        for idx, (name, a, b, delta, _) in enumerate(patterns):
            cx = section_width // 2 + idx * section_width
            cy = canvas.rows // 2 + 2
            scale = min(section_width // 4, canvas.rows // 5)

            # Draw curve
            for i in range(200):
                angle = (i / 200) * 2 * math.pi
                px = math.sin(a * angle + t + delta)
                py = math.sin(b * angle + t * 0.3)

                screen_x = int(cx + px * scale * 1.2)
                screen_y = int(cy + py * scale * 0.6)

                if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                    colors = ['cyan', 'yellow', 'magenta']
                    canvas.set_pixel(screen_x, screen_y, '●', colors[idx])

            # Label
            ratio = f"{int(a)}:{int(b)}"
            label_x = cx - len(name) // 2
            draw_info_overlay(canvas, [name], x=label_x, y=4, color='white')
            draw_info_overlay(canvas, [ratio], x=cx - len(ratio) // 2,
                              y=canvas.rows - 3, color='bright_yellow')

        yield canvas.render()


def generate_part2_frames(canvas: TerminalCanvas, fps: int
                          ) -> Generator[Image.Image, None, None]:
    """Generate all Part II frames."""
    yield from generate_part2_intro_frames(canvas, fps)
    yield from generate_pattern_showcase_frames(canvas, fps)
    yield from generate_ratio_comparison_frames(canvas, fps)


# =============================================================================
# PART III: PHASE AND FREQUENCY EXPLORATION
# =============================================================================

def generate_part3_intro_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate intro frames for Part III."""
    title_duration = 2.5
    total_frames = int(title_duration * fps)

    for frame in range(total_frames):
        canvas.clear()

        # Fade in effect
        alpha = min(1.0, frame / (fps * 0.5))

        if alpha > 0.3:
            draw_title_card(canvas, "PART III", "Phase & Frequency Exploration")

        if alpha > 0.6:
            draw_equation(canvas, canvas.rows - 5)

        yield canvas.render()


def generate_phase_sweep_frames(canvas: TerminalCanvas, a: float, b: float,
                                fps: int) -> Generator[Image.Image, None, None]:
    """Generate frames showing phase sweep from 0 to 2π.

    This demonstrates how phase affects curve shape at fixed frequencies.
    """
    duration = 8.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames

        # Sweep delta from 0 to 2π
        delta = progress * 2 * math.pi

        canvas.clear()

        # Draw the curve
        draw_lissajous(canvas, t * 1.5, a, b, delta, points=500, trail_length=6)

        # Overlay info
        ratio_str = f"{int(a)}:{int(b)}"
        delta_str = f"δ = {delta:.2f} rad ({math.degrees(delta):.0f}°)"
        info = [
            f"Ratio: {ratio_str}",
            delta_str,
            "───────────────",
            "Phase shifts the",
            "curve's starting",
            "point in time.",
        ]
        draw_info_overlay(canvas, info, x=2, y=1)

        # Progress bar
        bar_width = 30
        filled = int(progress * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        bar_line = f"δ: 0 [{bar}] 2π"
        draw_info_overlay(canvas, [bar_line], x=canvas.cols - len(bar_line) - 2,
                          y=canvas.rows - 2, color='cyan')

        yield canvas.render()


def generate_frequency_comparison_frames(canvas: TerminalCanvas, fps: int
                                         ) -> Generator[Image.Image, None, None]:
    """Generate frames comparing different frequency ratios.

    Shows how a:b ratio determines the pattern complexity.
    """
    time_per_ratio = 3.0

    for idx, (ratio_name, a, b, description) in enumerate(FREQUENCY_RATIOS):
        # Hold on this ratio
        hold_frames = int(time_per_ratio * fps)

        for frame in range(hold_frames):
            t = frame / fps
            delta = math.pi / 2  # Fixed phase for clean comparison

            canvas.clear()

            # Draw curve
            draw_lissajous(canvas, t * 2, a, b, delta, points=600, trail_length=5)

            # Ratio info
            info = [
                f"Ratio {ratio_name}",
                f"a={int(a)}, b={int(b)}",
                "─" * 20,
                description[:25],
            ]
            draw_info_overlay(canvas, info, x=2, y=1)

            # Draw small equation
            eq = f"x=sin({int(a)}t+π/2)  y=sin({int(b)}t)"
            draw_info_overlay(canvas, [eq], x=2, y=canvas.rows - 2, color='bright_green')

            yield canvas.render()

        # Transition to next ratio (fast morph)
        if idx < len(FREQUENCY_RATIOS) - 1:
            _, next_a, next_b, _ = FREQUENCY_RATIOS[idx + 1]

            trans_frames = int(0.5 * fps)
            for frame in range(trans_frames):
                t_trans = frame / fps
                progress = frame / trans_frames
                eased = ease_in_out_cubic(progress)

                curr_a = lerp(a, next_a, eased)
                curr_b = lerp(b, next_b, eased)

                canvas.clear()
                draw_lissajous(canvas, t_trans * 3, curr_a, curr_b, math.pi / 2,
                               points=500, trail_length=8)

                info = ["Transitioning..."]
                draw_info_overlay(canvas, info, x=2, y=1, color='yellow')

                yield canvas.render()


def generate_musical_intervals_frames(canvas: TerminalCanvas, fps: int
                                      ) -> Generator[Image.Image, None, None]:
    """Generate frames showing musical interval connections.

    Demonstrates how frequency ratios correspond to musical harmonics.
    """
    intervals = [
        ("1:1", 1.0, 1.0, "Unison"),
        ("1:2", 1.0, 2.0, "Octave"),
        ("2:3", 2.0, 3.0, "Perfect Fifth"),
        ("3:4", 3.0, 4.0, "Perfect Fourth"),
        ("4:5", 4.0, 5.0, "Major Third"),
        ("3:5", 3.0, 5.0, "Major Sixth"),
    ]

    time_per_interval = 2.5

    for ratio_name, a, b, interval_name in intervals:
        frames = int(time_per_interval * fps)

        for frame in range(frames):
            t = frame / fps

            canvas.clear()

            # Draw curve with rainbow palette
            draw_lissajous(canvas, t * 2, a, b, math.pi / 2, points=500,
                           trail_length=6, palette=THEMES['rainbow'])

            # Musical interval info
            info = [
                "♪ Musical Intervals ♪",
                "─" * 22,
                f"Ratio: {ratio_name}",
                f"Interval: {interval_name}",
                "",
                "Lissajous curves",
                "visualize the harmonic",
                "relationships in music!",
            ]
            draw_info_overlay(canvas, info, x=2, y=1)

            yield canvas.render()


def generate_part3_frames(canvas: TerminalCanvas, fps: int
                          ) -> Generator[Image.Image, None, None]:
    """Generate all Part III frames."""
    # Intro
    yield from generate_part3_intro_frames(canvas, fps)

    # Phase sweep demo (using 1:2 ratio - figure 8)
    yield from generate_phase_sweep_frames(canvas, 1.0, 2.0, fps)

    # Frequency comparison
    yield from generate_frequency_comparison_frames(canvas, fps)

    # Musical intervals connection
    yield from generate_musical_intervals_frames(canvas, fps)


# =============================================================================
# PART IV: REAL-WORLD APPLICATIONS
# =============================================================================

def generate_part4_intro_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate intro frames for Part IV."""
    title_duration = 2.5
    total_frames = int(title_duration * fps)

    for frame in range(total_frames):
        canvas.clear()
        alpha = min(1.0, frame / (fps * 0.5))

        if alpha > 0.3:
            draw_title_card(canvas, "PART IV", "Real-World Applications")

        yield canvas.render()


def draw_oscilloscope_frame(canvas: TerminalCanvas, t: float, a: float, b: float,
                            delta: float):
    """Draw oscilloscope-style display with grid."""
    # Draw grid
    grid_color = 'blue'
    cx = canvas.cols // 2
    cy = canvas.rows // 2

    # Horizontal and vertical center lines
    for x in range(canvas.cols):
        if x % 4 == 0:
            canvas.set_pixel(x, cy, '·', grid_color)
    for y in range(canvas.rows):
        if y % 2 == 0:
            canvas.set_pixel(cx, y, '·', grid_color)

    # Draw grid intersections
    for x in range(0, canvas.cols, 10):
        for y in range(0, canvas.rows, 5):
            canvas.set_pixel(x, y, '+', grid_color)

    # Draw the Lissajous pattern (bright green like CRT)
    scale_x = canvas.cols // 3
    scale_y = canvas.rows // 3
    points = 400

    for i in range(points):
        angle = (i / points) * 2 * math.pi
        px = math.sin(a * angle + t)
        py = math.sin(b * angle + delta + t * 0.3)

        screen_x = int(cx + px * scale_x * 1.2)
        screen_y = int(cy + py * scale_y * 0.7)

        if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
            # CRT phosphor effect - brighter at current position
            brightness = 1.0 - (abs(t % 1.0 - i / points))
            color = 'bright_green' if brightness > 0.7 else 'green'
            canvas.set_pixel(screen_x, screen_y, '●', color)


def generate_oscilloscope_demo_frames(canvas: TerminalCanvas, fps: int
                                      ) -> Generator[Image.Image, None, None]:
    """Generate oscilloscope XY mode demonstration."""
    duration = 6.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps

        canvas.clear()

        # Sweep through different phase relationships
        phase_progress = (frame / total_frames) * math.pi
        draw_oscilloscope_frame(canvas, t, 1.0, 2.0, phase_progress)

        # Oscilloscope info
        info = [
            "┌─ OSCILLOSCOPE XY ─┐",
            "│ CH1: Input A      │",
            "│ CH2: Input B      │",
            "│ Mode: X-Y Plot    │",
            "└──────────────────┘",
        ]
        draw_info_overlay(canvas, info, x=2, y=1, color='green')

        # Explanation
        explain = [
            "XY mode plots two",
            "signals against each",
            "other, revealing",
            "phase relationships.",
        ]
        draw_info_overlay(canvas, explain, x=2, y=canvas.rows - 5, color='white')

        yield canvas.render()


def generate_laser_show_frames(canvas: TerminalCanvas, fps: int
                               ) -> Generator[Image.Image, None, None]:
    """Generate laser show demonstration."""
    duration = 6.0
    total_frames = int(duration * fps)

    patterns = [
        (1.0, 1.0, "Circle scan"),
        (1.0, 2.0, "Figure-8 trace"),
        (2.0, 3.0, "Trefoil pattern"),
        (3.0, 5.0, "Pentagram burst"),
    ]

    frames_per_pattern = total_frames // len(patterns)

    for idx, (a, b, name) in enumerate(patterns):
        for frame in range(frames_per_pattern):
            t = frame / fps

            canvas.clear()

            # Laser-style rendering - bright beam with trails
            cx = canvas.cols // 2
            cy = canvas.rows // 2
            scale_x = canvas.cols // 3
            scale_y = canvas.rows // 3

            # Draw multiple trace lines for laser "beam" effect
            for trail in range(8):
                trail_t = t * 3 - trail * 0.02
                points = 300

                for i in range(points):
                    angle = (i / points) * 2 * math.pi
                    px = math.sin(a * angle + trail_t)
                    py = math.sin(b * angle + math.pi / 2 + trail_t * 0.5)

                    screen_x = int(cx + px * scale_x * 1.3)
                    screen_y = int(cy + py * scale_y * 0.8)

                    if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                        # Color gradient for laser effect
                        if trail == 0:
                            color = 'bright_white'
                            char = '●'
                        elif trail < 3:
                            color = 'bright_green'
                            char = '○'
                        else:
                            color = 'green'
                            char = '·'

                        canvas.set_pixel(screen_x, screen_y, char, color)

            # Info
            info = [
                "✦ LASER SHOW ✦",
                "─" * 16,
                f"Pattern: {name}",
                f"Ratio: {int(a)}:{int(b)}",
                "",
                "Galvanometer mirrors",
                "trace these patterns",
                "at high speed!",
            ]
            draw_info_overlay(canvas, info, x=2, y=1)

            yield canvas.render()


def generate_harmonograph_frames(canvas: TerminalCanvas, fps: int
                                 ) -> Generator[Image.Image, None, None]:
    """Generate harmonograph demonstration - mechanical pendulum drawing."""
    duration = 5.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames

        canvas.clear()

        # Harmonograph uses decaying oscillations
        decay = math.exp(-t * 0.3)

        cx = canvas.cols // 2
        cy = canvas.rows // 2
        scale_x = canvas.cols // 3
        scale_y = canvas.rows // 3

        # Draw accumulated path (pen trace)
        points = int(500 * progress) + 100
        for i in range(points):
            angle = (i / 200) * 2 * math.pi
            local_decay = math.exp(-angle * 0.05)

            # Slightly different frequencies create the harmonograph effect
            px = math.sin(2.01 * angle) * local_decay
            py = math.sin(3.0 * angle + math.pi / 4) * local_decay

            screen_x = int(cx + px * scale_x * decay)
            screen_y = int(cy + py * scale_y * 0.7 * decay)

            if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                # Ink density effect
                color = 'white' if i > points - 50 else 'bright_blue'
                char = '●' if i > points - 10 else '·'
                canvas.set_pixel(screen_x, screen_y, char, color)

        info = [
            "HARMONOGRAPH",
            "─" * 14,
            "Mechanical pendulums",
            "with pen attachment",
            "",
            "Damping creates the",
            "spiral-in effect.",
        ]
        draw_info_overlay(canvas, info, x=2, y=1)

        yield canvas.render()


def generate_part4_frames(canvas: TerminalCanvas, fps: int
                          ) -> Generator[Image.Image, None, None]:
    """Generate all Part IV frames."""
    yield from generate_part4_intro_frames(canvas, fps)
    yield from generate_oscilloscope_demo_frames(canvas, fps)
    yield from generate_laser_show_frames(canvas, fps)
    yield from generate_harmonograph_frames(canvas, fps)


# =============================================================================
# PART V: THE GAME
# =============================================================================

@dataclass
class GameEnemy:
    """Enemy following a Lissajous path."""
    a: float
    b: float
    delta: float
    name: str
    color: str
    speed: float = 1.0


GAME_ENEMIES = [
    GameEnemy(1.0, 1.0, math.pi / 2, "Orbiter", "cyan", 1.5),
    GameEnemy(1.0, 2.0, 0, "Swooper", "yellow", 2.0),
    GameEnemy(2.0, 3.0, 0, "Dancer", "magenta", 1.2),
    GameEnemy(3.0, 4.0, math.pi / 4, "Weaver", "bright_green", 0.8),
    GameEnemy(2.0, 5.0, 0, "Starmaker", "bright_red", 1.0),
]


def draw_player(canvas: TerminalCanvas, x: int, y: int):
    """Draw the player ship."""
    ship = [
        "  ▲  ",
        " ◄█► ",
        "  ▼  ",
    ]
    for dy, row in enumerate(ship):
        for dx, char in enumerate(row):
            if char != ' ':
                canvas.set_pixel(x + dx - 2, y + dy - 1, char, 'bright_white')


def draw_enemy(canvas: TerminalCanvas, x: int, y: int, enemy: GameEnemy, t: float):
    """Draw an enemy at position."""
    # Pulsing effect
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    char = '◆' if pulse > 0.5 else '◇'
    canvas.set_pixel(x, y, char, enemy.color)


def generate_part5_intro_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate intro frames for Part V."""
    title_duration = 2.5
    total_frames = int(title_duration * fps)

    for frame in range(total_frames):
        canvas.clear()
        alpha = min(1.0, frame / (fps * 0.5))

        if alpha > 0.3:
            draw_title_card(canvas, "PART V", "The Game - Lissajous Hunter")

        yield canvas.render()


def generate_enemy_showcase_frames(canvas: TerminalCanvas, fps: int
                                   ) -> Generator[Image.Image, None, None]:
    """Generate frames showcasing each enemy type."""
    time_per_enemy = 3.0

    for enemy in GAME_ENEMIES:
        frames = int(time_per_enemy * fps)

        for frame in range(frames):
            t = frame / fps

            canvas.clear()

            # Draw the enemy's Lissajous path
            cx = canvas.cols // 2
            cy = canvas.rows // 2
            scale_x = canvas.cols // 4
            scale_y = canvas.rows // 4

            # Path preview (faded)
            for i in range(200):
                angle = (i / 200) * 2 * math.pi
                px = math.sin(enemy.a * angle)
                py = math.sin(enemy.b * angle + enemy.delta)

                screen_x = int(cx + px * scale_x * 1.2)
                screen_y = int(cy + py * scale_y * 0.7)

                if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                    canvas.set_pixel(screen_x, screen_y, '·', 'blue')

            # Current enemy position
            angle = t * enemy.speed * 2
            ex = math.sin(enemy.a * angle)
            ey = math.sin(enemy.b * angle + enemy.delta)
            enemy_x = int(cx + ex * scale_x * 1.2)
            enemy_y = int(cy + ey * scale_y * 0.7)

            draw_enemy(canvas, enemy_x, enemy_y, enemy, t)

            # Enemy info
            info = [
                f"═══ {enemy.name} ═══",
                f"Pattern: {int(enemy.a)}:{int(enemy.b)}",
                f"Speed: {enemy.speed}x",
                "─" * 18,
                "Predict the path",
                "to intercept!",
            ]
            draw_info_overlay(canvas, info, x=2, y=1)

            yield canvas.render()


def generate_gameplay_demo_frames(canvas: TerminalCanvas, fps: int
                                  ) -> Generator[Image.Image, None, None]:
    """Generate gameplay demonstration frames."""
    duration = 8.0
    total_frames = int(duration * fps)

    # Player position (center-bottom)
    player_x = canvas.cols // 2
    player_y = canvas.rows - 5

    # Active enemies
    active_enemies = GAME_ENEMIES[:3]

    score = 0

    for frame in range(total_frames):
        t = frame / fps

        canvas.clear()

        # Draw play area border
        for x in range(canvas.cols):
            canvas.set_pixel(x, 0, '═', 'cyan')
            canvas.set_pixel(x, canvas.rows - 1, '═', 'cyan')
        for y in range(canvas.rows):
            canvas.set_pixel(0, y, '║', 'cyan')
            canvas.set_pixel(canvas.cols - 1, y, '║', 'cyan')

        # Draw each enemy
        cx = canvas.cols // 2
        cy = canvas.rows // 2 - 3

        for enemy in active_enemies:
            angle = t * enemy.speed * 1.5
            ex = math.sin(enemy.a * angle)
            ey = math.sin(enemy.b * angle + enemy.delta)

            enemy_x = int(cx + ex * (canvas.cols // 4))
            enemy_y = int(cy + ey * (canvas.rows // 4) * 0.6)

            # Draw path hint
            if frame % 30 < 15:  # Flashing path hints
                for i in range(50):
                    hint_angle = angle + (i / 50) * 0.5
                    hx = math.sin(enemy.a * hint_angle)
                    hy = math.sin(enemy.b * hint_angle + enemy.delta)
                    hint_x = int(cx + hx * (canvas.cols // 4))
                    hint_y = int(cy + hy * (canvas.rows // 4) * 0.6)
                    if 1 < hint_x < canvas.cols - 1 and 1 < hint_y < canvas.rows - 1:
                        canvas.set_pixel(hint_x, hint_y, '·', 'blue')

            draw_enemy(canvas, enemy_x, enemy_y, enemy, t)

        # Draw player (moves in sine wave for demo)
        demo_player_x = int(player_x + math.sin(t * 2) * 15)
        draw_player(canvas, demo_player_x, player_y)

        # Score display
        score = int(t * 100)
        score_str = f"SCORE: {score:05d}"
        draw_info_overlay(canvas, [score_str], x=3, y=1, color='bright_yellow')

        # Lives
        lives_str = "♥ ♥ ♥"
        draw_info_overlay(canvas, [lives_str], x=canvas.cols - len(lives_str) - 3,
                          y=1, color='bright_red')

        yield canvas.render()


def generate_part5_frames(canvas: TerminalCanvas, fps: int
                          ) -> Generator[Image.Image, None, None]:
    """Generate all Part V frames."""
    yield from generate_part5_intro_frames(canvas, fps)
    yield from generate_enemy_showcase_frames(canvas, fps)
    yield from generate_gameplay_demo_frames(canvas, fps)


# =============================================================================
# FULL SERIES
# =============================================================================

def generate_series_title_frames(canvas: TerminalCanvas, fps: int
                                 ) -> Generator[Image.Image, None, None]:
    """Generate opening title for full series."""
    duration = 3.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Animated background pattern
        cx = canvas.cols // 2
        cy = canvas.rows // 2

        # Light background animation
        for i in range(100):
            angle = (i / 100) * 2 * math.pi
            px = math.sin(3 * angle + t)
            py = math.sin(4 * angle + t * 0.5)

            x = int(cx + px * (canvas.cols // 3))
            y = int(cy + py * (canvas.rows // 3) * 0.5)

            if 0 <= x < canvas.cols and 0 <= y < canvas.rows:
                canvas.set_pixel(x, y, '·', 'blue')

        draw_title_card(canvas, "LISSAJOUS", "A Mathematical Journey")

        yield canvas.render()


def generate_series_credits_frames(canvas: TerminalCanvas, fps: int
                                   ) -> Generator[Image.Image, None, None]:
    """Generate closing credits."""
    duration = 3.0
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        canvas.clear()

        credits = [
            "Thanks for watching!",
            "",
            "LISSAJOUS EXPLORER",
            "───────────────────",
            "Created with",
            "atari-style",
            "",
            "github.com/jcaldwell-labs/atari-style",
        ]

        start_y = (canvas.rows - len(credits)) // 2
        for i, line in enumerate(credits):
            x = (canvas.cols - len(line)) // 2
            color = 'bright_cyan' if i == 2 else 'white'
            for j, char in enumerate(line):
                canvas.set_pixel(x + j, start_y + i, char, color)

        yield canvas.render()


def generate_full_series_frames(canvas: TerminalCanvas, fps: int
                                ) -> Generator[Image.Image, None, None]:
    """Generate the complete 5-part educational series."""
    yield from generate_series_title_frames(canvas, fps)
    yield from generate_part1_frames(canvas, fps)
    yield from generate_part2_frames(canvas, fps)
    yield from generate_part3_frames(canvas, fps)
    yield from generate_part4_frames(canvas, fps)
    yield from generate_part5_frames(canvas, fps)
    yield from generate_series_credits_frames(canvas, fps)


# =============================================================================
# PREVIEW MODE
# =============================================================================

@dataclass
class PreviewOptions:
    """Options for quick preview rendering."""
    enabled: bool = False
    fps: int = 5  # Low FPS for fast preview
    start_time: float = 0.0  # Start time in seconds
    end_time: Optional[float] = None  # End time in seconds (None = no limit)
    max_duration: float = 5.0  # Max duration when no end_time specified


def add_preview_watermark(frame: Image.Image) -> Image.Image:
    """Add PREVIEW watermark to frame."""
    from PIL import ImageDraw, ImageFont

    # Create a copy to avoid modifying original
    watermarked = frame.copy()
    draw = ImageDraw.Draw(watermarked)

    # Watermark text
    text = "PREVIEW"

    # Try to use a larger monospace font across platforms, fall back to default
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",  # Linux
        "/System/Library/Fonts/Monaco.ttf",  # macOS
        "C:/Windows/Fonts/consolab.ttf",  # Windows Consolas Bold
        "C:/Windows/Fonts/consola.ttf",  # Windows Consolas Regular
        "C:/Windows/Fonts/lucon.ttf",  # Windows Lucida Console
    ]
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, 24)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position in top-right corner with padding
    x = frame.width - text_width - 10
    y = 10

    # Draw background (RGB - no alpha needed since we're on RGB image)
    padding = 5
    draw.rectangle(
        [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
        fill=(0, 0, 0)
    )

    # Draw text in bright yellow
    draw.text((x, y), text, font=font, fill=(255, 255, 0))

    return watermarked


def filter_frames_for_preview(
    frames: Generator[Image.Image, None, None],
    fps: int,
    preview: PreviewOptions
) -> Generator[Image.Image, None, None]:
    """Filter frames based on preview options.

    Args:
        frames: Original frame generator
        fps: Original FPS of the content
        preview: Preview options including time range

    Yields:
        Filtered and watermarked frames
    """
    # Calculate frame indices to avoid floating point issues
    start_frame = int(preview.start_time * fps)

    # Calculate effective end time
    if preview.end_time is not None:
        end_frame = int(preview.end_time * fps)
    elif preview.start_time > 0:
        # If start specified but no end, use start + max_duration
        end_frame = int((preview.start_time + preview.max_duration) * fps)
    else:
        # Default: just use max_duration from start
        end_frame = int(preview.max_duration * fps)

    frames_yielded = 0
    frame_idx = 0

    for frame in frames:
        # Stop at end frame (check first, before yielding)
        if frame_idx >= end_frame:
            break

        # Skip frames before start frame
        if frame_idx < start_frame:
            frame_idx += 1
            continue

        # Add watermark and yield
        yield add_preview_watermark(frame)
        frames_yielded += 1
        frame_idx += 1

    # Print summary
    duration = frames_yielded / fps if fps > 0 else 0
    end_time = frame_idx / fps if fps > 0 else 0
    print(f"Preview: {frames_yielded} frames ({duration:.1f}s) "
          f"from {preview.start_time:.1f}s to {end_time:.1f}s")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Lissajous Educational Series - Complete 5-Part Video Course",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preview mode examples:
  --preview                    Quick 5s preview at 5 FPS
  --preview --start 10         Preview 5s starting at 10s mark
  --preview --start 10 --end 20  Preview from 10s to 20s
  --preview --duration 15      Preview first 15s at 5 FPS
"""
    )

    parser.add_argument('-o', '--output', default='lissajous_education.gif',
                        help='Output GIF path')
    parser.add_argument('--cols', type=int, default=133,
                        help='Terminal columns (default: 133)')
    parser.add_argument('--rows', type=int, default=37,
                        help='Terminal rows (default: 37)')
    parser.add_argument('--fps', type=int, default=15,
                        help='Frames per second (default: 15)')

    part_group = parser.add_mutually_exclusive_group(required=True)
    part_group.add_argument('--part', type=int, choices=[1, 2, 3, 4, 5],
                            help='Render specific part (1-5)')
    part_group.add_argument('--full-series', action='store_true',
                            help='Render the complete 5-part series')

    # Preview mode options
    preview_group = parser.add_argument_group('preview options')
    preview_group.add_argument('--preview', action='store_true',
                               help='Enable preview mode (5 FPS, limited duration, watermarked)')
    preview_group.add_argument('--start', type=float, default=0.0,
                               help='Start time in seconds (default: 0)')
    preview_group.add_argument('--end', type=float, default=None,
                               help='End time in seconds (default: start + duration)')
    preview_group.add_argument('--duration', type=float, default=5.0,
                               help='Max preview duration in seconds (default: 5)')

    args = parser.parse_args()

    # Build preview options
    preview = PreviewOptions(
        enabled=args.preview,
        fps=5 if args.preview else args.fps,
        start_time=args.start,
        end_time=args.end,
        max_duration=args.duration
    )

    # Use preview FPS if in preview mode
    render_fps = preview.fps if preview.enabled else args.fps

    canvas = TerminalCanvas(cols=args.cols, rows=args.rows)

    print(f"Canvas: {canvas.cols}x{canvas.rows} chars = "
          f"{canvas.img_width}x{canvas.img_height} pixels")

    if preview.enabled:
        print(f"PREVIEW MODE: {preview.fps} FPS, "
              f"start={preview.start_time}s, "
              f"end={preview.end_time or f'start+{preview.max_duration}s'}")

    if args.part == 1:
        print("Rendering Part I: Introduction to Lissajous Curves")
        frames = generate_part1_frames(canvas, args.fps)
    elif args.part == 2:
        print("Rendering Part II: The Pattern Gallery")
        frames = generate_part2_frames(canvas, args.fps)
    elif args.part == 3:
        print("Rendering Part III: Phase & Frequency Exploration")
        frames = generate_part3_frames(canvas, args.fps)
    elif args.part == 4:
        print("Rendering Part IV: Real-World Applications")
        frames = generate_part4_frames(canvas, args.fps)
    elif args.part == 5:
        print("Rendering Part V: The Game")
        frames = generate_part5_frames(canvas, args.fps)
    else:  # args.full_series (required=True ensures one option is set)
        print("Rendering Full Series (Parts I-V)")
        frames = generate_full_series_frames(canvas, args.fps)

    # Apply preview filtering if enabled
    if preview.enabled:
        frames = filter_frames_for_preview(frames, args.fps, preview)

    success = render_gif(args.output, frames, render_fps)
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
