"""Lissajous Criticality Explorer - Find and follow stable patterns.

Explores Lissajous parameter space, detecting when parameters approach
critical ratios that produce recognizable, stable patterns like circles,
figure-8s, trefoils, and stars.

Uses higher-order feedback (velocity, acceleration) to navigate toward
or orbit around stable configurations, similar to FluxControlExplorer.
"""

import os
import time
import math
import subprocess
from dataclasses import dataclass
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from ...core.renderer import Color


# Critical Lissajous ratios and their properties
@dataclass
class CriticalPattern:
    """A stable Lissajous pattern at specific parameter ratios."""
    name: str
    a: float  # x frequency
    b: float  # y frequency
    delta: float  # phase offset (radians)
    description: str
    stability_radius: float = 0.15  # How close params must be to "lock"


CRITICAL_PATTERNS = [
    CriticalPattern("Circle", 1.0, 1.0, math.pi/2, "Perfect rotating circle", 0.1),
    CriticalPattern("Ellipse", 1.0, 1.0, math.pi/4, "Tilted ellipse", 0.1),
    CriticalPattern("Figure-8", 1.0, 2.0, 0, "Infinity symbol", 0.12),
    CriticalPattern("Parabola", 1.0, 2.0, math.pi/2, "Bow-tie shape", 0.12),
    CriticalPattern("Trefoil", 2.0, 3.0, 0, "Three-leaf clover", 0.15),
    CriticalPattern("Fish", 2.0, 3.0, math.pi/2, "Fish-like curve", 0.15),
    CriticalPattern("Quatrefoil", 3.0, 4.0, 0, "Four-leaf pattern", 0.15),
    CriticalPattern("Star-5", 2.0, 5.0, 0, "Five-pointed star", 0.18),
    CriticalPattern("Lemniscate", 1.0, 2.0, math.pi/4, "Figure-8 variant", 0.12),
    CriticalPattern("Pentagram", 3.0, 5.0, 0, "Complex star", 0.18),
]


# Color palettes
PALETTE_COOL = [Color.BLUE, Color.CYAN, Color.BRIGHT_CYAN, Color.WHITE, Color.BRIGHT_WHITE]
PALETTE_WARM = [Color.RED, Color.YELLOW, Color.BRIGHT_YELLOW, Color.WHITE, Color.BRIGHT_WHITE]
PALETTE_AURORA = [Color.GREEN, Color.BRIGHT_GREEN, Color.CYAN, Color.MAGENTA, Color.BRIGHT_WHITE]

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


class CriticalityTracker:
    """Tracks proximity to critical Lissajous patterns."""

    def __init__(self):
        self.patterns = CRITICAL_PATTERNS
        self.current_a = 1.0
        self.current_b = 1.0
        self.current_delta = math.pi / 2

        # Velocity tracking for smooth navigation
        self.velocity_a = 0.0
        self.velocity_b = 0.0
        self.velocity_delta = 0.0

        # History for pattern detection
        self.proximity_history: List[float] = []
        self.locked_pattern: Optional[CriticalPattern] = None
        self.lock_time = 0.0

    def find_nearest_pattern(self) -> Tuple[CriticalPattern, float]:
        """Find the nearest critical pattern and distance to it."""
        best_pattern = None
        best_distance = float('inf')

        for pattern in self.patterns:
            # Normalize ratio comparison
            ratio_current = self.current_a / self.current_b if self.current_b != 0 else 0
            ratio_pattern = pattern.a / pattern.b if pattern.b != 0 else 0

            # Distance in parameter space
            ratio_dist = abs(ratio_current - ratio_pattern)
            delta_dist = abs(self.current_delta - pattern.delta) / math.pi

            # Combined distance (weighted)
            distance = math.sqrt(ratio_dist**2 + delta_dist**2 * 0.5)

            if distance < best_distance:
                best_distance = distance
                best_pattern = pattern

        return best_pattern, best_distance

    def is_near_criticality(self) -> bool:
        """Check if currently near any critical pattern."""
        pattern, distance = self.find_nearest_pattern()
        return distance < pattern.stability_radius

    def get_lock_strength(self) -> float:
        """Get strength of lock to nearest pattern (0-1)."""
        pattern, distance = self.find_nearest_pattern()
        if distance >= pattern.stability_radius:
            return 0.0
        return 1.0 - (distance / pattern.stability_radius)

    def update(self, dt: float, mode: str = "explore"):
        """Update parameters based on exploration mode.

        Modes:
        - "explore": Wander through parameter space
        - "seek": Move toward nearest critical pattern
        - "orbit": Circle around current critical pattern
        """
        pattern, distance = self.find_nearest_pattern()
        lock_strength = self.get_lock_strength()

        if mode == "explore":
            # Brownian-like exploration with drift toward interesting regions
            self.velocity_a += (math.sin(time.time() * 0.7) * 0.1 - self.velocity_a * 0.1) * dt
            self.velocity_b += (math.cos(time.time() * 0.5) * 0.1 - self.velocity_b * 0.1) * dt
            self.velocity_delta += (math.sin(time.time() * 0.3) * 0.2 - self.velocity_delta * 0.1) * dt

        elif mode == "seek":
            # Move toward nearest critical pattern
            target_ratio = pattern.a / pattern.b
            current_ratio = self.current_a / self.current_b if self.current_b != 0 else 1

            ratio_error = target_ratio - current_ratio
            delta_error = pattern.delta - self.current_delta

            # PD control toward target
            self.velocity_a += ratio_error * 0.5 * dt
            self.velocity_b += -ratio_error * 0.3 * dt
            self.velocity_delta += delta_error * 0.5 * dt

        elif mode == "orbit":
            # Orbit around the critical point
            if lock_strength > 0.5:
                # Small oscillations around stable point
                orbit_freq = 0.5
                self.velocity_a = math.sin(time.time() * orbit_freq) * 0.05 * (1 - lock_strength)
                self.velocity_b = math.cos(time.time() * orbit_freq * 1.3) * 0.05 * (1 - lock_strength)
                self.velocity_delta = math.sin(time.time() * orbit_freq * 0.7) * 0.1 * (1 - lock_strength)

        # Apply velocities with damping
        damping = 0.95
        self.velocity_a *= damping
        self.velocity_b *= damping
        self.velocity_delta *= damping

        self.current_a += self.velocity_a * dt * 10
        self.current_b += self.velocity_b * dt * 10
        self.current_delta += self.velocity_delta * dt * 5

        # Clamp to reasonable ranges
        self.current_a = max(0.5, min(5.0, self.current_a))
        self.current_b = max(0.5, min(5.0, self.current_b))
        self.current_delta = self.current_delta % (2 * math.pi)

        # Track lock state
        if lock_strength > 0.7:
            if self.locked_pattern != pattern:
                self.locked_pattern = pattern
                self.lock_time = 0.0
            self.lock_time += dt
        else:
            self.locked_pattern = None
            self.lock_time = 0.0


class MockRenderer:
    def __init__(self, width: int = 120, height: int = 40):
        self.width = width
        self.height = height
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.color_buffer = [[None for _ in range(width)] for _ in range(height)]

    def clear_buffer(self):
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = ' '
                self.color_buffer[y][x] = None

    def set_pixel(self, x: int, y: int, char: str, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color


class LissajousExplorerRenderer:
    def __init__(self, width: int = 120, height: int = 40, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cell_width = 14
        self.cell_height = 26
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height
        self.mock_renderer = MockRenderer(width, height)
        self.bg_color = (20, 22, 30)

        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
        except:
            self.font = ImageFont.load_default()
            self.font_small = self.font

    def render_frame(self) -> Image.Image:
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for y in range(self.height):
            for x in range(self.width):
                char = self.mock_renderer.buffer[y][x]
                if char == ' ':
                    continue
                color = self.mock_renderer.color_buffer[y][x]
                rgb = COLOR_RGB.get(color, (248, 248, 242))
                px = x * self.cell_width
                py = y * self.cell_height
                draw.text((px, py), char, font=self.font, fill=rgb)

        return img

    def add_status_overlay(self, img: Image.Image, tracker: CriticalityTracker, t: float) -> Image.Image:
        draw = ImageDraw.Draw(img)

        pattern, distance = tracker.find_nearest_pattern()
        lock_strength = tracker.get_lock_strength()

        # Status bar at bottom
        bar_y = self.img_height - 60
        draw.rectangle([(0, bar_y), (self.img_width, self.img_height)], fill=(25, 27, 35))

        # Lock strength bar
        bar_width = int(200 * lock_strength)
        if lock_strength > 0.7:
            bar_color = (80, 250, 123)  # Green - locked
        elif lock_strength > 0.3:
            bar_color = (241, 250, 140)  # Yellow - approaching
        else:
            bar_color = (98, 114, 164)  # Blue - exploring

        draw.rectangle([(10, bar_y + 10), (10 + bar_width, bar_y + 25)], fill=bar_color)
        draw.rectangle([(10, bar_y + 10), (210, bar_y + 25)], outline=(80, 80, 100))

        # Pattern info
        status = "LOCKED" if lock_strength > 0.7 else "SEEKING" if lock_strength > 0.3 else "EXPLORING"
        text = f"{status}: {pattern.name} ({pattern.description})"
        draw.text((220, bar_y + 8), text, font=self.font_small, fill=(139, 233, 253))

        # Parameters
        params = f"a={tracker.current_a:.2f} b={tracker.current_b:.2f} δ={tracker.current_delta:.2f} | ratio={tracker.current_a/tracker.current_b:.3f}"
        draw.text((10, bar_y + 35), params, font=self.font_small, fill=(255, 121, 198))

        # Time
        draw.text((self.img_width - 100, bar_y + 35), f"t={t:.1f}s", font=self.font_small, fill=(150, 150, 150))

        return img


def draw_lissajous(renderer: MockRenderer, a: float, b: float, delta: float,
                   t: float, palette: List, trail_length: int = 60):
    """Draw Lissajous curve with motion trail."""
    cx = renderer.width // 2
    cy = renderer.height // 2
    scale_x = renderer.width // 3
    scale_y = renderer.height // 3

    # Draw trail (older = dimmer)
    for trail in range(trail_length):
        trail_t = t - trail * 0.015
        alpha = 1.0 - (trail / trail_length)

        for i in range(150):
            angle = (i / 150) * 2 * math.pi + trail_t * 2

            x = math.sin(a * angle + delta)
            y = math.sin(b * angle)

            screen_x = int(cx + x * scale_x * 1.8)
            screen_y = int(cy + y * scale_y * 0.9)

            if not (0 <= screen_x < renderer.width and 0 <= screen_y < renderer.height):
                continue

            # Character and color based on trail depth
            if trail < 10:
                char = '●'
                color_idx = min(len(palette) - 1, 4)
            elif trail < 25:
                char = '○'
                color_idx = min(len(palette) - 1, 3)
            elif trail < 40:
                char = '∘'
                color_idx = min(len(palette) - 1, 2)
            else:
                char = '·'
                color_idx = min(len(palette) - 1, 1)

            # Color shift based on position in curve
            color_idx = (color_idx + i // 30) % len(palette)
            renderer.set_pixel(screen_x, screen_y, char, palette[color_idx])


def render_lissajous_exploration(duration: int = 60, output_path: str = None):
    """Render the Lissajous criticality exploration journey."""
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/lissajous-explorer.mp4"

    frames_dir = "/tmp/lissajous_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = LissajousExplorerRenderer(width=120, height=40, fps=30)
    tracker = CriticalityTracker()

    fps = renderer.fps
    total_frames = duration * fps
    dt = 1.0 / fps

    # Exploration schedule: cycle through modes
    def get_mode(t):
        cycle = t % 20  # 20 second cycles
        if cycle < 8:
            return "explore"
        elif cycle < 14:
            return "seek"
        else:
            return "orbit"

    print(f"Rendering LISSAJOUS EXPLORER: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()
    discoveries = []

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        # Get current mode
        mode = get_mode(t)

        # Update tracker
        tracker.update(dt, mode)

        # Choose palette based on lock strength
        lock_strength = tracker.get_lock_strength()
        if lock_strength > 0.7:
            palette = PALETTE_AURORA  # Locked - aurora colors
        elif lock_strength > 0.3:
            palette = PALETTE_WARM  # Approaching - warm colors
        else:
            palette = PALETTE_COOL  # Exploring - cool colors

        # Draw Lissajous curve
        draw_lissajous(
            renderer.mock_renderer,
            tracker.current_a,
            tracker.current_b,
            tracker.current_delta,
            t,
            palette
        )

        # Log discoveries
        if tracker.locked_pattern and tracker.lock_time < dt * 2:
            discoveries.append((t, tracker.locked_pattern.name))

        # Render frame
        img = renderer.render_frame()
        img = renderer.add_status_overlay(img, tracker, t)

        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 200 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            pattern, _ = tracker.find_nearest_pattern()
            print(f"  Frame {frame_num + 1}/{total_frames} | Mode: {mode:7} | Near: {pattern.name:12} | FPS: {fps_actual:.1f}")

    print(f"\nDiscoveries: {len(discoveries)}")
    for t, name in discoveries[:10]:
        print(f"  t={t:.1f}s: {name}")

    print(f"\nCreating video...")

    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size = os.path.getsize(output_path)
        print(f"Success! {output_path} ({size / 1024 / 1024:.1f} MB)")
        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))
        return True
    return False


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    render_lissajous_exploration(duration)
