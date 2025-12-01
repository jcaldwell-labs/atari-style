"""Composite Animation Video Renderer - Direct frame-to-video for composites."""

import os
import time
import subprocess
import math
from PIL import Image, ImageDraw, ImageFont


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
        """Clear the rendering buffer."""
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = ' '
                self.color_buffer[y][x] = None

    def set_pixel(self, x: int, y: int, char: str = '█', color=None):
        """Set a character in the buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color

    def draw_text(self, x: int, y: int, text: str, color=None):
        """Draw text at position."""
        for i, char in enumerate(text):
            self.set_pixel(x + i, y, char, color)

    def render(self):
        """No-op for mock renderer."""
        pass

    def enter_fullscreen(self):
        """No-op for mock renderer."""
        pass

    def exit_fullscreen(self):
        """No-op for mock renderer."""
        pass


class CompositeVideoRenderer:
    """Renders composite animations directly to video frames."""

    def __init__(self, width: int = 120, height: int = 40, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

        # Cell dimensions for rendering
        self.cell_width = 14
        self.cell_height = 26

        # Image dimensions
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height

        # Create mock renderer
        self.mock_renderer = MockRenderer(width, height)

        # Load monospace font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 22)
            except:
                self.font = ImageFont.load_default()

        # Background color (Dracula)
        self.bg_color = (40, 42, 54)

    def render_frame_to_image(self) -> Image.Image:
        """Render current buffer to PIL Image."""
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for y in range(self.height):
            for x in range(self.width):
                char = self.mock_renderer.buffer[y][x]
                if char == ' ':
                    continue

                color = self.mock_renderer.color_buffer[y][x]
                rgb = COLOR_MAP.get(color, (248, 248, 242))  # Default white

                px = x * self.cell_width
                py = y * self.cell_height

                draw.text((px, py), char, font=self.font, fill=rgb)

        return img


def render_composite_video(
    composite_class,
    duration: int = 30,
    output_path: str = None,
    title: str = "Composite"
):
    """Render a composite animation to video.

    Args:
        composite_class: The composite animation class to render
        duration: Duration in seconds
        output_path: Output file path
        title: Title for progress display
    """
    if output_path is None:
        output_path = f"/tmp/{title.lower().replace(' ', '-')}.mp4"

    frames_dir = "/tmp/composite_frames"
    os.makedirs(frames_dir, exist_ok=True)

    # Clean up old frames
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    # Initialize renderer
    renderer = CompositeVideoRenderer(width=120, height=40, fps=30)

    # Create composite animation with mock renderer
    composite = composite_class(renderer.mock_renderer)

    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering {title}: {total_frames} frames at {fps} FPS")
    print(f"Output: {output_path}")
    print(f"Frame size: {renderer.img_width}x{renderer.img_height}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps
        dt = 1.0 / fps

        # Clear buffer
        renderer.mock_renderer.clear_buffer()

        # Update and draw composite
        composite.update(dt)
        composite.draw(t)

        # Render to image
        img = renderer.render_frame_to_image()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 100 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            eta = (total_frames - frame_num - 1) / fps_actual
            print(f"  Frame {frame_num + 1}/{total_frames} ({fps_actual:.1f} fps, ETA: {eta:.0f}s)")

    print(f"\nAll frames rendered. Creating video with ffmpeg...")

    # Use ffmpeg to create video
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

        # Clean up frames
        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))

        return True
    else:
        print(f"Error creating video: {result.stderr}")
        return False


def render_plasma_lissajous(duration: int = 30, output_path: str = None):
    """Render PlasmaLissajous composite demo."""
    from .screensaver import PlasmaLissajous
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/plasma-lissajous-demo.mp4"
    return render_composite_video(PlasmaLissajous, duration, output_path, "PlasmaLissajous")


def render_flux_spiral(duration: int = 30, output_path: str = None):
    """Render FluxSpiral composite demo."""
    from .screensaver import FluxSpiral
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/flux-spiral-demo.mp4"
    return render_composite_video(FluxSpiral, duration, output_path, "FluxSpiral")


def render_lissajous_plasma(duration: int = 30, output_path: str = None):
    """Render LissajousPlasma composite demo."""
    from .screensaver import LissajousPlasma
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/lissajous-plasma-demo.mp4"
    return render_composite_video(LissajousPlasma, duration, output_path, "LissajousPlasma")


def render_all_composites(duration: int = 30):
    """Render all three composite demos."""
    print("=" * 60)
    print("RENDERING ALL COMPOSITE ANIMATION DEMOS")
    print("=" * 60)
    print()

    render_plasma_lissajous(duration)
    print()

    render_flux_spiral(duration)
    print()

    render_lissajous_plasma(duration)
    print()

    print("=" * 60)
    print("ALL COMPOSITE DEMOS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    render_all_composites(duration)
