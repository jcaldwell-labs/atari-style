"""Self-Tuning Video Renderer - Animations that stay interesting.

Uses InterestingnessTracker to monitor and adjust parameters,
avoiding boring attractors and keeping the visual display dynamic.
"""

import os
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

from .interestingness_tracker import (
    InterestingnessTracker, InterestingnessBounds,
    BOUNDS_FLUID, BOUNDS_GEOMETRIC, BOUNDS_PLASMA
)


# ANSI color to RGB mapping (Dracula-like theme)
COLOR_MAP = {
    'red': (255, 85, 85),
    'green': (80, 250, 123),
    'yellow': (241, 250, 140),
    'blue': (189, 147, 249),
    'magenta': (255, 121, 198),
    'cyan': (139, 233, 253),
    'white': (248, 248, 242),
    'bright_red': (255, 110, 110),
    'bright_green': (105, 255, 148),
    'bright_yellow': (255, 255, 165),
    'bright_blue': (210, 170, 255),
    'bright_magenta': (255, 146, 218),
    'bright_cyan': (164, 255, 255),
    'bright_white': (255, 255, 255),
}


class MockRenderer:
    """Mock renderer that captures pixels for video rendering."""

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

    def set_pixel(self, x: int, y: int, char: str = '█', color=None):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color

    def draw_text(self, x: int, y: int, text: str, color=None):
        for i, char in enumerate(text):
            self.set_pixel(x + i, y, char, color)

    def render(self):
        pass

    def enter_fullscreen(self):
        pass

    def exit_fullscreen(self):
        pass


class SelfTuningVideoRenderer:
    """Renders animations with self-tuning to stay interesting."""

    def __init__(self, width: int = 120, height: int = 40, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cell_width = 14
        self.cell_height = 26
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height
        self.mock_renderer = MockRenderer(width, height)

        # Load font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 22)
            except:
                self.font = ImageFont.load_default()

        self.bg_color = (40, 42, 54)

    def render_frame_to_image(self, status_text: str = None) -> Image.Image:
        """Render buffer to PIL Image, optionally with status overlay."""
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for y in range(self.height):
            for x in range(self.width):
                char = self.mock_renderer.buffer[y][x]
                if char == ' ':
                    continue
                color = self.mock_renderer.color_buffer[y][x]
                rgb = COLOR_MAP.get(color, (248, 248, 242))
                px = x * self.cell_width
                py = y * self.cell_height
                draw.text((px, py), char, font=self.font, fill=rgb)

        # Add status overlay if provided
        if status_text:
            # Semi-transparent bar at bottom
            bar_height = 30
            overlay = Image.new('RGBA', (self.img_width, bar_height), (0, 0, 0, 180))
            img.paste(Image.alpha_composite(
                Image.new('RGBA', overlay.size, self.bg_color + (255,)),
                overlay
            ).convert('RGB'), (0, self.img_height - bar_height))

            draw = ImageDraw.Draw(img)
            draw.text((10, self.img_height - bar_height + 5), status_text,
                     font=self.font, fill=(139, 233, 253))

        return img


def render_self_tuning_composite(
    composite_class,
    duration: int = 60,
    output_path: str = None,
    title: str = "SelfTuning",
    bounds: InterestingnessBounds = None,
    show_status: bool = True
):
    """Render a composite animation with self-tuning.

    The animation continuously monitors its "interestingness" and adjusts
    parameters to avoid boring states.
    """
    if output_path is None:
        output_path = f"/tmp/{title.lower().replace(' ', '-')}.mp4"

    frames_dir = "/tmp/selftune_frames"
    os.makedirs(frames_dir, exist_ok=True)

    # Clean up old frames
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    # Initialize
    renderer = SelfTuningVideoRenderer(width=120, height=40, fps=30)
    composite = composite_class(renderer.mock_renderer)
    tracker = InterestingnessTracker(bounds or BOUNDS_FLUID)

    fps = renderer.fps
    total_frames = duration * fps
    dt = 1.0 / fps

    # Tuning state
    last_tune_time = 0.0
    tune_interval = 1.0  # Check every second
    tune_log = []

    print(f"Rendering {title} with self-tuning: {total_frames} frames at {fps} FPS")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps

        # Clear and render
        renderer.mock_renderer.clear_buffer()
        composite.update(dt)
        composite.draw(t)

        # Sample modulation value from composite
        mod_value = None
        if hasattr(composite, 'source') and hasattr(composite.source, 'get_global_value'):
            mod_value = composite.source.get_global_value(t)

        # Track interestingness
        tracker.sample_frame(
            renderer.mock_renderer.buffer,
            renderer.mock_renderer.color_buffer,
            mod_value
        )

        # Self-tune periodically
        if t - last_tune_time > tune_interval:
            suggestion = tracker.get_adjustment_suggestion()

            if suggestion['action'] != 'none':
                # Apply adjustment based on composite type
                _apply_tuning(composite, suggestion)
                tune_log.append({
                    'time': t,
                    'action': suggestion['action'],
                    'reason': suggestion['reason'],
                    'magnitude': suggestion['magnitude']
                })

            last_tune_time = t

        # Generate status text
        status = None
        if show_status:
            m = tracker.metrics
            diagnosis = tracker.get_diagnosis()
            status = f"t={t:.1f}s | Score:{m.overall_score:.2f} | Cov:{m.coverage:.0f}% | {diagnosis}"

        # Render to image
        img = renderer.render_frame_to_image(status)
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 100 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            eta = (total_frames - frame_num - 1) / fps_actual
            m = tracker.metrics
            print(f"  Frame {frame_num + 1}/{total_frames} | "
                  f"Score: {m.overall_score:.2f} | "
                  f"FPS: {fps_actual:.1f} | ETA: {eta:.0f}s")

    print(f"\nAll frames rendered. Creating video...")

    # FFmpeg
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
        print(f"\nSuccess! Video saved to: {output_path}")
        print(f"File size: {size / 1024 / 1024:.1f} MB")

        # Print tuning log summary
        if tune_log:
            print(f"\nTuning adjustments made: {len(tune_log)}")
            for entry in tune_log[:5]:
                print(f"  t={entry['time']:.1f}s: {entry['action']} ({entry['reason']})")
            if len(tune_log) > 5:
                print(f"  ... and {len(tune_log) - 5} more")

        # Clean up
        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))

        return True
    else:
        print(f"Error: {result.stderr}")
        return False


def _apply_tuning(composite, suggestion: dict):
    """Apply tuning suggestion to composite animation."""
    action = suggestion['action']
    magnitude = suggestion['magnitude']

    # Get source animation (the modulator)
    source = getattr(composite, 'source', None)
    target = getattr(composite, 'target', None)

    if action == 'increase_energy':
        # For FluxSpiral: increase rain rate
        if hasattr(source, 'rain_rate'):
            source.rain_rate = min(5.0, source.rain_rate * (1 + magnitude))
        # For other composites: increase modulation strength
        if hasattr(composite, 'modulation_strength'):
            composite.modulation_strength = min(2.0, composite.modulation_strength * (1 + magnitude * 0.5))

    elif action == 'decrease_energy':
        if hasattr(source, 'rain_rate'):
            source.rain_rate = max(0.1, source.rain_rate * (1 - magnitude * 0.5))
        # Drain if available
        if hasattr(source, 'drain_global'):
            source.drain_global(0.3)

    elif action == 'increase_dynamics':
        # Increase wave speed, rotation, or other dynamic parameters
        if hasattr(source, 'wave_speed'):
            source.wave_speed = min(1.0, source.wave_speed * (1 + magnitude * 0.3))
        if hasattr(target, 'rotation_speed'):
            target.rotation_speed = min(5.0, target.rotation_speed * (1 + magnitude * 0.5))
        # Increase rain for more activity
        if hasattr(source, 'rain_rate'):
            source.rain_rate = min(5.0, source.rain_rate * (1 + magnitude * 0.5))

    elif action == 'decrease_dynamics':
        if hasattr(source, 'wave_speed'):
            source.wave_speed = max(0.1, source.wave_speed * (1 - magnitude * 0.3))
        if hasattr(source, 'damping'):
            source.damping = min(0.98, source.damping + magnitude * 0.02)

    elif action == 'increase_modulation':
        # Boost modulation strength
        if hasattr(composite, 'modulation_strength'):
            composite.modulation_strength = min(2.5, composite.modulation_strength * (1 + magnitude))
        # Increase source activity to generate more variation
        if hasattr(source, 'rain_rate'):
            source.rain_rate = min(5.0, source.rain_rate * (1 + magnitude * 0.8))
        if hasattr(source, 'wave_speed'):
            source.wave_speed = min(1.0, source.wave_speed * (1 + magnitude * 0.4))


def render_self_tuning_flux_spiral(duration: int = 60, output_path: str = None):
    """Render FluxSpiral with self-tuning."""
    from .screensaver import FluxSpiral
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/flux-spiral-selftuned.mp4"

    # Use fluid bounds - need decent coverage and activity
    bounds = InterestingnessBounds(
        coverage_min=15, coverage_max=50, coverage_sweet=30,
        activity_min=0.5, activity_max=12.0, activity_sweet=3.0,
        modulation_range_min=0.25
    )

    # Custom factory to pre-configure FluxSpiral for better dynamics
    def create_flux_spiral(renderer):
        composite = FluxSpiral(renderer)
        # Much higher rain rate for visible fluid activity
        composite.source.rain_rate = 3.0  # Was 0.5
        composite.source.wave_speed = 0.6  # Was 0.4
        composite.source.drop_strength = 15.0  # Was 10.0
        composite.modulation_strength = 1.5  # Stronger modulation

        # Pre-warm the fluid simulation
        for _ in range(100):
            composite.source.update(0.05)

        return composite

    return render_self_tuning_composite(
        create_flux_spiral, duration, output_path,
        title="FluxSpiral-SelfTuned",
        bounds=bounds
    )


def render_self_tuning_plasma_lissajous(duration: int = 60, output_path: str = None):
    """Render PlasmaLissajous with self-tuning."""
    from .screensaver import PlasmaLissajous
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/plasma-lissajous-selftuned.mp4"

    # Geometric bounds - lower coverage is fine
    bounds = InterestingnessBounds(
        coverage_min=5, coverage_max=35, coverage_sweet=15,
        activity_min=0.2, activity_max=8.0, activity_sweet=1.5,
        modulation_range_min=0.2
    )

    return render_self_tuning_composite(
        PlasmaLissajous, duration, output_path,
        title="PlasmaLissajous-SelfTuned",
        bounds=bounds
    )


def render_self_tuning_all(duration: int = 60):
    """Render all composites with self-tuning."""
    print("=" * 60)
    print("SELF-TUNING COMPOSITE RENDERS")
    print("=" * 60)
    print()

    render_self_tuning_flux_spiral(duration)
    print()
    render_self_tuning_plasma_lissajous(duration)
    print()

    print("=" * 60)
    print("ALL SELF-TUNING RENDERS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    render_self_tuning_all(duration)
