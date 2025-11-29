"""Themed Video Renderer - Beautiful animations with nature palettes."""

import os
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
from ..core.renderer import Color


# Theme palettes
OCEAN = [
    Color.BLUE, Color.BLUE, Color.CYAN,
    Color.CYAN, Color.BRIGHT_CYAN, Color.BRIGHT_CYAN,
    Color.BRIGHT_WHITE,
]

FOREST = [
    Color.GREEN, Color.GREEN, Color.BRIGHT_GREEN,
    Color.BRIGHT_GREEN, Color.YELLOW, Color.BRIGHT_YELLOW,
    Color.BRIGHT_WHITE,
]

DESERT = [
    Color.RED, Color.YELLOW, Color.YELLOW,
    Color.BRIGHT_YELLOW, Color.BRIGHT_YELLOW,
    Color.WHITE, Color.BRIGHT_WHITE,
]

# Dracula-inspired RGB colors
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

# Theme-specific background colors
THEME_BG = {
    'ocean': (20, 30, 50),      # Deep blue
    'forest': (20, 35, 25),     # Dark green
    'desert': (45, 35, 25),     # Warm brown
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


class ThemedVideoRenderer:
    """Renders themed animations to video."""

    def __init__(self, width: int = 120, height: int = 40, fps: int = 30, theme: str = 'ocean'):
        self.width = width
        self.height = height
        self.fps = fps
        self.theme = theme
        self.cell_width = 14
        self.cell_height = 26
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height
        self.mock_renderer = MockRenderer(width, height)
        self.bg_color = THEME_BG.get(theme, (40, 42, 54))

        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
        except:
            self.font = ImageFont.load_default()

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


def render_themed_lissajous(theme: str = 'ocean', duration: int = 30, output_path: str = None):
    """Render Lissajous curves with themed palette.

    Creates organic, flowing curves that morph over time.
    """
    if output_path is None:
        output_path = f"/home/be-dev-agent/projects/jcaldwell-labs/media/output/{theme}-lissajous.mp4"

    palette = {'ocean': OCEAN, 'forest': FOREST, 'desert': DESERT}.get(theme, OCEAN)

    frames_dir = "/tmp/themed_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = ThemedVideoRenderer(width=120, height=40, fps=30, theme=theme)
    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering {theme.upper()} Lissajous: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        # Slowly evolving Lissajous parameters
        a = 3 + math.sin(t * 0.3) * 2  # Range 1-5
        b = 4 + math.cos(t * 0.25) * 2  # Range 2-6
        delta = t * 0.5  # Phase shift

        cx = renderer.width // 2
        cy = renderer.height // 2
        scale_x = renderer.width // 3
        scale_y = renderer.height // 3

        # Draw multiple overlapping curves with trail effect
        for trail in range(80):
            trail_t = t - trail * 0.02
            phase = trail_t * 2

            for i in range(200):
                angle = (i / 200) * 2 * math.pi
                x = int(cx + scale_x * math.sin(a * angle + phase))
                y = int(cy + scale_y * math.sin(b * angle + delta + phase * 0.5))

                if 0 <= x < renderer.width and 0 <= y < renderer.height:
                    # Color based on position in curve and trail depth
                    color_idx = (i + trail * 3) % len(palette)
                    # Fade older trails
                    if trail < 20:
                        renderer.mock_renderer.set_pixel(x, y, '●', palette[color_idx])
                    elif trail < 40:
                        renderer.mock_renderer.set_pixel(x, y, '○', palette[min(color_idx, len(palette)-2)])
                    else:
                        renderer.mock_renderer.set_pixel(x, y, '·', palette[0])

        img = renderer.render_frame()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 150 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            print(f"  Frame {frame_num + 1}/{total_frames} ({fps_actual:.1f} fps)")

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


def render_themed_waves(theme: str = 'ocean', duration: int = 30, output_path: str = None):
    """Render flowing wave patterns with themed palette.

    Creates smooth, ocean-like wave animations.
    """
    if output_path is None:
        output_path = f"/home/be-dev-agent/projects/jcaldwell-labs/media/output/{theme}-waves.mp4"

    palette = {'ocean': OCEAN, 'forest': FOREST, 'desert': DESERT}.get(theme, OCEAN)
    chars = ['·', '∘', '○', '◎', '●', '◉', '█']

    frames_dir = "/tmp/themed_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = ThemedVideoRenderer(width=120, height=40, fps=30, theme=theme)
    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering {theme.upper()} Waves: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        for y in range(renderer.height):
            for x in range(renderer.width):
                # Multiple overlapping sine waves
                wave1 = math.sin(x * 0.08 + t * 2) * math.cos(y * 0.15 + t * 0.5)
                wave2 = math.sin(x * 0.05 - t * 1.5 + y * 0.1) * 0.7
                wave3 = math.cos((x + y) * 0.06 + t * 0.8) * 0.5
                wave4 = math.sin(math.sqrt(x*x + y*y) * 0.04 - t * 1.2) * 0.4

                value = (wave1 + wave2 + wave3 + wave4) / 2.6  # Normalize to ~[-1, 1]

                if abs(value) < 0.15:
                    continue

                # Map value to character and color
                intensity = (value + 1) / 2  # 0 to 1
                char_idx = min(len(chars) - 1, int(intensity * len(chars)))
                color_idx = min(len(palette) - 1, int(intensity * len(palette)))

                renderer.mock_renderer.set_pixel(x, y, chars[char_idx], palette[color_idx])

        img = renderer.render_frame()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 150 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            print(f"  Frame {frame_num + 1}/{total_frames} ({fps_actual:.1f} fps)")

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


def render_themed_spiral(theme: str = 'ocean', duration: int = 30, output_path: str = None):
    """Render expanding/contracting spiral with themed palette."""
    if output_path is None:
        output_path = f"/home/be-dev-agent/projects/jcaldwell-labs/media/output/{theme}-spiral.mp4"

    palette = {'ocean': OCEAN, 'forest': FOREST, 'desert': DESERT}.get(theme, OCEAN)

    frames_dir = "/tmp/themed_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = ThemedVideoRenderer(width=120, height=40, fps=30, theme=theme)
    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering {theme.upper()} Spiral: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        cx = renderer.width // 2
        cy = renderer.height // 2

        # Multiple spirals with different speeds
        for spiral_idx in range(4):
            spiral_offset = spiral_idx * math.pi / 2
            rotation = t * (1.5 + spiral_idx * 0.3) + spiral_offset

            # Breathing effect
            scale = 1.0 + 0.3 * math.sin(t * 0.8 + spiral_idx)

            for i in range(300):
                angle = i * 0.08 + rotation
                r = (i * 0.15 + 2) * scale

                # Aspect ratio correction
                x = int(cx + r * math.cos(angle) * 1.8)
                y = int(cy + r * math.sin(angle) * 0.9)

                if 0 <= x < renderer.width and 0 <= y < renderer.height:
                    # Color cycles along spiral
                    color_idx = (i // 15 + spiral_idx * 2) % len(palette)
                    char = '●' if i % 3 == 0 else '○'
                    renderer.mock_renderer.set_pixel(x, y, char, palette[color_idx])

        img = renderer.render_frame()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 150 == 0:
            elapsed = time.time() - start_time
            fps_actual = (frame_num + 1) / elapsed
            print(f"  Frame {frame_num + 1}/{total_frames} ({fps_actual:.1f} fps)")

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


def render_all_themes(duration: int = 30):
    """Render all theme variations."""
    print("=" * 60)
    print("THEMED ANIMATION RENDERS")
    print("=" * 60)
    print()

    themes = ['ocean', 'forest', 'desert']

    for theme in themes:
        print(f"\n{'='*40}")
        print(f"THEME: {theme.upper()}")
        print('='*40)
        render_themed_waves(theme, duration)
        print()

    print("\n" + "=" * 60)
    print("ALL THEMED RENDERS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    render_all_themes(duration)
