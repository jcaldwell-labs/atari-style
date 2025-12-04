#!/usr/bin/env python3
"""Lissajous Educational Series - Parts III-V.

Renders educational video segments explaining Lissajous curve mathematics:
- Part III: Phase and Frequency Exploration
- Part IV: Real-World Applications
- Part V: Complete Game Demo

Usage:
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 3 -o phase.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 4 -o applications.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --part 5 -o game.gif
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --full-series -o full_series.gif
"""

import math
from dataclasses import dataclass
from typing import Generator, List, Tuple

from PIL import Image, ImageDraw

from .lissajous_terminal_gif import (
    TerminalCanvas, draw_lissajous, render_gif,
    ease_in_out_cubic, lerp, PATTERNS, THEMES, COLOR_RGB
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

    for ratio_name, a, b, description in FREQUENCY_RATIOS:
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
        if ratio_name != FREQUENCY_RATIOS[-1][0]:
            next_idx = FREQUENCY_RATIOS.index((ratio_name, a, b, description)) + 1
            _, next_a, next_b, _ = FREQUENCY_RATIOS[next_idx]

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
            "github.com/jcaldwell-labs",
            "/atari-style",
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
    """Generate the complete educational series."""
    yield from generate_series_title_frames(canvas, fps)
    yield from generate_part3_frames(canvas, fps)
    yield from generate_part4_frames(canvas, fps)
    yield from generate_part5_frames(canvas, fps)
    yield from generate_series_credits_frames(canvas, fps)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Lissajous Educational Series - Parts III-V"
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
    part_group.add_argument('--part', type=int, choices=[3, 4, 5],
                            help='Render specific part (3, 4, or 5)')
    part_group.add_argument('--full-series', action='store_true',
                            help='Render the complete series')

    args = parser.parse_args()

    canvas = TerminalCanvas(cols=args.cols, rows=args.rows)

    print(f"Canvas: {canvas.cols}x{canvas.rows} chars = "
          f"{canvas.img_width}x{canvas.img_height} pixels")

    if args.part == 3:
        print("Rendering Part III: Phase & Frequency Exploration")
        frames = generate_part3_frames(canvas, args.fps)
    elif args.part == 4:
        print("Rendering Part IV: Real-World Applications")
        frames = generate_part4_frames(canvas, args.fps)
    elif args.part == 5:
        print("Rendering Part V: The Game")
        frames = generate_part5_frames(canvas, args.fps)
    elif args.full_series:
        print("Rendering Full Series (Parts III-V)")
        frames = generate_full_series_frames(canvas, args.fps)
    else:
        parser.print_help()
        return 1

    success = render_gif(args.output, frames, args.fps)
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
