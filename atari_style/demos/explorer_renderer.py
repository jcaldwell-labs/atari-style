"""Explorer Renderer - Watch the system discover interesting patterns.

Visualizes parameter exploration as a journey through configuration space.
Shows both the modulation source and target, with real-time metrics.
"""

import os
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

from .interestingness_tracker import InterestingnessTracker, InterestingnessBounds


# Dracula color palette
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
    """Mock renderer for video capture."""

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

    def render(self):
        pass

    def enter_fullscreen(self):
        pass

    def exit_fullscreen(self):
        pass


class ExplorerRenderer:
    """Renders exploration journey to video."""

    def __init__(self, width: int = 120, height: int = 40, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cell_width = 14
        self.cell_height = 26
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height

        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
        except:
            self.font = ImageFont.load_default()
            self.font_small = self.font

        self.bg_color = (40, 42, 54)

    def render_dual_layer(self, source_buffer, source_colors,
                         target_buffer, target_colors) -> Image.Image:
        """Render both source (dim) and target (bright) layers."""
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Draw source layer (dimmed)
        for y in range(len(source_buffer)):
            for x in range(len(source_buffer[0])):
                char = source_buffer[y][x]
                if char == ' ':
                    continue
                color = source_colors[y][x]
                rgb = COLOR_MAP.get(color, (100, 100, 100))
                # Dim the source layer
                rgb = tuple(int(c * 0.3) for c in rgb)
                px = x * self.cell_width
                py = y * self.cell_height
                draw.text((px, py), char, font=self.font, fill=rgb)

        # Draw target layer (full brightness)
        for y in range(len(target_buffer)):
            for x in range(len(target_buffer[0])):
                char = target_buffer[y][x]
                if char == ' ':
                    continue
                color = target_colors[y][x]
                rgb = COLOR_MAP.get(color, (248, 248, 242))
                px = x * self.cell_width
                py = y * self.cell_height
                draw.text((px, py), char, font=self.font, fill=rgb)

        return img

    def add_metrics_overlay(self, img: Image.Image, metrics: dict) -> Image.Image:
        """Add metrics panel overlay."""
        draw = ImageDraw.Draw(img)

        # Bottom status bar
        bar_y = self.img_height - 35
        draw.rectangle([(0, bar_y), (self.img_width, self.img_height)],
                      fill=(30, 32, 44))

        # Score bar visualization
        score = metrics.get('score', 0)
        bar_width = int(200 * score)
        bar_color = (255, 85, 85) if score < 0.4 else (241, 250, 140) if score < 0.7 else (80, 250, 123)
        draw.rectangle([(10, bar_y + 8), (10 + bar_width, bar_y + 20)], fill=bar_color)
        draw.rectangle([(10, bar_y + 8), (210, bar_y + 20)], outline=(100, 100, 100))

        # Metrics text
        text = (f"Score: {score:.2f} | "
               f"Cov: {metrics.get('coverage', 0):.0f}% | "
               f"Activity: {metrics.get('activity', 0):.1f} | "
               f"ModRange: {metrics.get('mod_range', 0):.2f}")
        draw.text((220, bar_y + 5), text, font=self.font_small, fill=(139, 233, 253))

        # Parameter display on right
        params = metrics.get('params', {})
        if params:
            param_text = " | ".join(f"{k}:{v:.2f}" for k, v in params.items())
            draw.text((700, bar_y + 5), param_text, font=self.font_small, fill=(255, 121, 198))

        return img


def render_flux_spiral_explorer(duration: int = 60, output_path: str = None):
    """Render FluxSpiral showing both fluid and spiral layers.

    The fluid lattice is shown as a dim background, with the spiral
    overlay showing modulation effects.
    """
    from .screensaver import SpiralAnimation
    from .flux_control_zen import FluidLattice

    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/flux-spiral-explorer.mp4"

    frames_dir = "/tmp/explorer_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    # Separate renderers for each layer
    renderer = ExplorerRenderer(width=120, height=40, fps=30)
    source_mock = MockRenderer(120, 40)
    target_mock = MockRenderer(120, 40)

    # Create animations
    fluid = FluidLattice(120, 40)
    spiral = SpiralAnimation(target_mock)

    # Configure for 40% coverage equilibrium (sweet spot)
    # Using calibrated formula from FluxControlExplorer
    fluid.rain_rate = 1.2
    fluid.wave_speed = 0.45
    fluid.damping = 0.79  # From equilibrium for 40% target
    fluid.drop_strength = 10.0

    spiral.num_spirals = 4
    spiral.tightness = 8.0
    spiral.rotation_speed = 1.0

    # Light pre-warm (don't saturate)
    for _ in range(30):
        fluid.update(0.05)

    # Tracking
    tracker = InterestingnessTracker(InterestingnessBounds(
        coverage_min=20, coverage_max=70, coverage_sweet=45,
        activity_min=1.0, activity_max=15.0, activity_sweet=5.0,
        modulation_range_min=0.3
    ))

    fps = renderer.fps
    total_frames = duration * fps
    dt = 1.0 / fps

    print(f"Rendering FluxSpiral Explorer: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps

        # Update fluid
        fluid.update(dt)

        # Get modulation value from fluid
        mod_value = fluid.get_global_value(t) if hasattr(fluid, 'get_global_value') else 0

        # Alternative: calculate activity from fluid state
        total_energy = sum(abs(fluid.current[y][x])
                          for y in range(fluid.height)
                          for x in range(fluid.width))
        mod_value = min(1.0, max(-1.0, total_energy / 5000 - 0.5))

        # Modulate spiral parameters
        spiral.rotation_speed = 0.5 + (mod_value + 1) * 1.5  # Range 0.5-3.5
        spiral.tightness = 6.0 + (mod_value + 1) * 3.0  # Range 6-12

        # Clear and draw source (fluid) layer
        source_mock.clear_buffer()
        chars = ['·', '∘', '○', '◎', '●', '◉']
        colors = ['blue', 'cyan', 'bright_cyan', 'white', 'bright_white', 'bright_white']
        for y in range(fluid.height):
            for x in range(fluid.width):
                val = abs(fluid.current[y][x])
                if val < 0.3:  # Low threshold to see wave structure
                    continue
                idx = min(len(chars) - 1, int(val / 1.2))  # Scale for variation
                source_mock.set_pixel(x, y, chars[idx], colors[idx])

        # Draw target (spiral) layer
        target_mock.clear_buffer()
        spiral.draw(t)

        # Track combined buffers for metrics
        # Merge buffers for coverage calculation
        combined_buffer = [[' ' for _ in range(120)] for _ in range(40)]
        for y in range(40):
            for x in range(120):
                if source_mock.buffer[y][x] != ' ':
                    combined_buffer[y][x] = source_mock.buffer[y][x]
                if target_mock.buffer[y][x] != ' ':
                    combined_buffer[y][x] = target_mock.buffer[y][x]

        tracker.sample_frame(combined_buffer, None, mod_value)

        # Render dual layer
        img = renderer.render_dual_layer(
            source_mock.buffer, source_mock.color_buffer,
            target_mock.buffer, target_mock.color_buffer
        )

        # Add metrics
        metrics = {
            'score': tracker.metrics.overall_score,
            'coverage': tracker.metrics.coverage,
            'activity': tracker.metrics.activity_variance,
            'mod_range': tracker.metrics.modulation_range,
            'params': {
                'rain': fluid.rain_rate,
                'wave': fluid.wave_speed,
                'rot': spiral.rotation_speed
            }
        }
        img = renderer.add_metrics_overlay(img, metrics)

        # Save frame
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        # Auto-tune based on metrics
        if frame_num % 30 == 0 and frame_num > 0:  # Every second
            suggestion = tracker.get_adjustment_suggestion()
            if suggestion['action'] == 'increase_energy':
                fluid.rain_rate = min(5.0, fluid.rain_rate * 1.2)
            elif suggestion['action'] == 'decrease_energy':
                fluid.rain_rate = max(0.5, fluid.rain_rate * 0.8)
                fluid.drain_global(0.2)
            elif suggestion['action'] == 'increase_dynamics':
                fluid.wave_speed = min(0.9, fluid.wave_speed * 1.15)
                fluid.rain_rate = min(5.0, fluid.rain_rate * 1.1)

        if (frame_num + 1) % 100 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            m = tracker.metrics
            print(f"  Frame {frame_num + 1}/{total_frames} | "
                  f"Score: {m.overall_score:.2f} | Cov: {m.coverage:.0f}% | "
                  f"rain={fluid.rain_rate:.1f} | "
                  f"FPS: {fps_actual:.1f}")

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
        print(f"\nSuccess! {output_path}")
        print(f"Size: {size / 1024 / 1024:.1f} MB")

        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))
        return True
    else:
        print(f"Error: {result.stderr}")
        return False


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    render_flux_spiral_explorer(duration)
