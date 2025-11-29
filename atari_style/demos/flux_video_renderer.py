"""Flux Video Renderer - Direct frame-to-video rendering (bypasses VHS)."""

import os
import time
import subprocess
from PIL import Image, ImageDraw, ImageFont
from .flux_showcase import FluxShowcase, CHARS_WAVE, OCEAN, FIRE, RAINBOW, SUNSET, DESERT


# ANSI color to RGB mapping (Dracula-like theme)
COLOR_MAP = {
    0: (40, 42, 54),      # Default/background
    1: (255, 85, 85),     # RED
    2: (80, 250, 123),    # GREEN
    3: (241, 250, 140),   # YELLOW
    4: (189, 147, 249),   # BLUE
    5: (255, 121, 198),   # MAGENTA
    6: (139, 233, 253),   # CYAN
    7: (248, 248, 242),   # WHITE
    9: (255, 110, 110),   # BRIGHT_RED
    10: (105, 255, 148),  # BRIGHT_GREEN
    11: (255, 255, 165),  # BRIGHT_YELLOW
    12: (210, 170, 255),  # BRIGHT_BLUE
    13: (255, 146, 218),  # BRIGHT_MAGENTA
    14: (164, 255, 255),  # BRIGHT_CYAN
    15: (255, 255, 255),  # BRIGHT_WHITE
}

# Map Color enum values to their ANSI codes
COLOR_TO_ANSI = {
    1: 1,   # RED
    2: 2,   # GREEN
    3: 3,   # YELLOW
    4: 4,   # BLUE
    5: 5,   # MAGENTA
    6: 6,   # CYAN
    7: 7,   # WHITE
    9: 9,   # BRIGHT_RED
    10: 10, # BRIGHT_GREEN
    11: 11, # BRIGHT_YELLOW
    12: 12, # BRIGHT_BLUE
    13: 13, # BRIGHT_MAGENTA
    14: 14, # BRIGHT_CYAN
    15: 15, # BRIGHT_WHITE
}


class FrameBuffer:
    """In-memory frame buffer for rendering."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.chars = [[' ' for _ in range(width)] for _ in range(height)]
        self.colors = [[0 for _ in range(width)] for _ in range(height)]

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.chars[y][x] = ' '
                self.colors[y][x] = 0

    def set_pixel(self, x: int, y: int, char: str, color: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.chars[y][x] = char
            self.colors[y][x] = color


class FluxVideoRenderer:
    """Renders Flux animation directly to video frames."""

    def __init__(self, width: int = 160, height: int = 45, fps: int = 20):
        self.width = width
        self.height = height
        self.fps = fps

        # Cell dimensions for rendering
        self.cell_width = 12
        self.cell_height = 24

        # Image dimensions
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height

        # Create frame buffer
        self.buffer = FrameBuffer(width, height)

        # Load monospace font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 20)
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
                char = self.buffer.chars[y][x]
                if char == ' ':
                    continue

                color_code = self.buffer.colors[y][x]
                rgb = COLOR_MAP.get(color_code, (248, 248, 242))

                px = x * self.cell_width
                py = y * self.cell_height

                draw.text((px, py), char, font=self.font, fill=rgb)

        return img


def render_flux_video(duration: int = 60, output_path: str = None):
    """Render Flux showcase directly to MP4 video.

    Args:
        duration: Duration in seconds
        output_path: Output file path (default: flux-direct-render.mp4)
    """
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/flux-direct-render.mp4"

    frames_dir = "/tmp/flux_frames"
    os.makedirs(frames_dir, exist_ok=True)

    # Clean up old frames
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    # Initialize renderer and showcase
    renderer = FluxVideoRenderer(width=160, height=45, fps=20)

    # Create a mock FluxShowcase that uses our buffer
    from .flux_control_zen import FluidLattice

    fluid = FluidLattice(renderer.width, renderer.height)
    fluid.wave_speed = 0.45
    fluid.damping = 0.77
    fluid.rain_rate = 0.5

    # Visual settings sequence (matching showcase)
    modes = [
        ('ocean', OCEAN, CHARS_WAVE, 0.3),
        ('fire', RAINBOW, CHARS_WAVE, 0.6),  # Use rainbow for more color
        ('rainbow', RAINBOW, CHARS_WAVE, 0.8),
        ('sunset', SUNSET, CHARS_WAVE, 0.4),
        ('ocean', OCEAN, CHARS_WAVE, 0.3),
    ]

    fps = 20
    total_frames = duration * fps
    segment_frames = total_frames // len(modes)

    print(f"Rendering {total_frames} frames at {fps} FPS")
    print(f"Output: {output_path}")
    print(f"Frame size: {renderer.img_width}x{renderer.img_height}")
    print()

    start_time = time.time()
    frame_count = 0

    for mode_idx, (mode_name, palette, char_set, color_speed) in enumerate(modes):
        segment_start = mode_idx * segment_frames
        segment_end = (mode_idx + 1) * segment_frames if mode_idx < len(modes) - 1 else total_frames

        print(f"Segment {mode_idx + 1}/{len(modes)}: {mode_name} ({segment_end - segment_start} frames)")

        for frame_num in range(segment_start, segment_end):
            # Update fluid simulation
            fluid.update(0.05)

            # Clear buffer
            renderer.buffer.clear()

            # Render fluid to buffer
            t = frame_num / fps  # Time in seconds

            for y in range(renderer.height):
                for x in range(renderer.width):
                    energy = fluid.current[y][x]
                    if energy > 0.02:
                        # Get character based on energy
                        char_idx = min(int(energy * len(char_set) * 2), len(char_set) - 1)
                        char = char_set[char_idx]

                        # Get color based on mode
                        if mode_name in ('rainbow', 'fire'):
                            # Rainbow cycling
                            phase = (t * color_speed + x * 0.02 + y * 0.015) % 1.0
                            color = palette[int(phase * len(palette)) % len(palette)]
                        else:
                            # Energy-based coloring
                            color_idx = min(int(energy * len(palette) * 2), len(palette) - 1)
                            color = palette[color_idx]

                        # Map Color enum to ANSI code
                        ansi_code = COLOR_TO_ANSI.get(color, 7)
                        renderer.buffer.set_pixel(x, y, char, ansi_code)

            # Render to image and save
            img = renderer.render_frame_to_image()
            frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
            img.save(frame_path)

            frame_count += 1
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps_actual = frame_count / elapsed
                eta = (total_frames - frame_count) / fps_actual
                print(f"  Frame {frame_count}/{total_frames} ({fps_actual:.1f} fps, ETA: {eta:.0f}s)")

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
        print(f"\nSuccess! Video saved to: {output_path}")

        # Get file size
        size = os.path.getsize(output_path)
        print(f"File size: {size / 1024 / 1024:.1f} MB")

        # Clean up frames
        print("Cleaning up temporary frames...")
        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))

        return True
    else:
        print(f"Error creating video: {result.stderr}")
        return False


def run_direct_render(duration: int = 60):
    """Entry point for direct video rendering."""
    render_flux_video(duration)


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    render_flux_video(duration)
