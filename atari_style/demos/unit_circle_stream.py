"""Unit Circle Educational Demo - Memory-Efficient Streaming Version.

This version pipes frames directly to ffmpeg to avoid:
1. Memory exhaustion from storing frame lists
2. Disk space issues from thousands of PNG files
3. WSL/system crashes

Usage:
    python -m atari_style.demos.unit_circle_stream
    python -m atari_style.demos.unit_circle_stream --preview  # 720p, 15fps
    python -m atari_style.demos.unit_circle_stream --output my-video.mp4
"""

import os
import sys
import math
import subprocess
import platform
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Generator, List

# Dracula-inspired color palette
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
    'comment': (98, 114, 164),
    'prompt': (80, 250, 123),
}


def find_monospace_font(size: int) -> ImageFont.FreeTypeFont:
    """Find a monospace font that works on the current platform."""
    font_paths = []

    if platform.system() == 'Windows':
        font_paths = [
            "C:/Windows/Fonts/consola.ttf",      # Consolas
            "C:/Windows/Fonts/cour.ttf",         # Courier New
            "C:/Windows/Fonts/lucon.ttf",        # Lucida Console
        ]
    elif platform.system() == 'Darwin':  # macOS
        font_paths = [
            "/System/Library/Fonts/Monaco.ttf",
            "/System/Library/Fonts/Menlo.ttc",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    # Fallback to default
    return ImageFont.load_default()


class StreamingRenderer:
    """Memory-efficient renderer that yields frames one at a time."""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.bg_color = (30, 32, 44)

        # Scale font sizes based on resolution
        scale = min(width / 1920, height / 1080)
        self.font_large = find_monospace_font(int(32 * scale))
        self.font_medium = find_monospace_font(int(24 * scale))
        self.font_small = find_monospace_font(int(18 * scale))
        self.font_code = find_monospace_font(int(20 * scale))

    def new_frame(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        return img, ImageDraw.Draw(img)

    def draw_unit_circle(self, draw: ImageDraw.Draw, cx: int, cy: int, radius: int,
                        theta: float, show_coords: bool = True):
        """Draw unit circle with rotating point."""
        # Axes
        draw.line([(cx - radius - 20, cy), (cx + radius + 20, cy)], fill=(60, 60, 80), width=1)
        draw.line([(cx, cy - radius - 20), (cx, cy + radius + 20)], fill=(60, 60, 80), width=1)

        # Circle
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                    outline=COLOR_RGB['cyan'], width=2)

        # Point position
        px = cx + int(radius * math.cos(theta))
        py = cy - int(radius * math.sin(theta))

        # Radial line
        draw.line([(cx, cy), (px, py)], fill=COLOR_RGB['bright_green'], width=3)

        # Point
        draw.ellipse([(px - 8, py - 8), (px + 8, py + 8)], fill=COLOR_RGB['bright_yellow'])
        draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=COLOR_RGB['white'])

        if show_coords:
            # sin line (vertical)
            draw.line([(px, cy), (px, py)], fill=COLOR_RGB['magenta'], width=2)
            # cos line (horizontal)
            draw.line([(cx, py), (px, py)], fill=COLOR_RGB['cyan'], width=2)

            draw.text((px + 10, (cy + py) // 2), "sin", font=self.font_small, fill=COLOR_RGB['magenta'])
            draw.text(((cx + px) // 2, py + 10), "cos", font=self.font_small, fill=COLOR_RGB['cyan'])

        draw.text((cx + 15, cy + 15), f"{math.degrees(theta):.0f} deg", font=self.font_medium, fill=COLOR_RGB['yellow'])
        return px, py

    def draw_sine_wave(self, draw: ImageDraw.Draw, x_start: int, y_center: int,
                      width: int, height: int, phase: float):
        """Draw sine wave."""
        draw.line([(x_start, y_center), (x_start + width, y_center)], fill=(60, 60, 80), width=1)

        prev = None
        for x in range(width):
            t = (x / width) * 2 * math.pi
            y = y_center - int(height/2 * math.sin(t + phase))
            if prev:
                draw.line([prev, (x_start + x, y)], fill=COLOR_RGB['cyan'], width=2)
            prev = (x_start + x, y)

        # Highlight current phase
        hx = x_start + int((phase % (2 * math.pi)) / (2 * math.pi) * width)
        hy = y_center - int(height/2 * math.sin(phase))
        draw.ellipse([(hx - 6, hy - 6), (hx + 6, hy + 6)], fill=COLOR_RGB['bright_yellow'])


def generate_ghost_typing_frames(renderer: StreamingRenderer, commands: List[str],
                                  duration: float, fps: int) -> Generator[Image.Image, None, None]:
    """Generate ghost typing frames one at a time."""
    total_frames = int(duration * fps)
    total_chars = sum(len(cmd) for cmd in commands)
    chars_per_second = total_chars / (duration * 0.7)

    lines = []
    for cmd in commands:
        line_type = 'comment' if cmd.startswith('#') else 'prompt' if cmd.startswith('$') else 'command'
        lines.append({'text': cmd, 'chars_shown': 0, 'type': line_type, 'active': False})

    current_line = 0
    char_acc = 0.0

    for frame in range(total_frames):
        img, draw = renderer.new_frame()

        # Update typing
        if current_line < len(lines):
            lines[current_line]['active'] = True
            char_acc += chars_per_second / fps

            while char_acc >= 1 and current_line < len(lines):
                if lines[current_line]['chars_shown'] < len(lines[current_line]['text']):
                    lines[current_line]['chars_shown'] += 1
                    char_acc -= 1
                else:
                    lines[current_line]['active'] = False
                    current_line += 1
                    if current_line < len(lines):
                        lines[current_line]['active'] = True
                    char_acc = 0
                    break

        # Draw
        y = int(renderer.height * 0.1)
        line_height = int(renderer.height * 0.03)
        cursor_on = (frame // 15) % 2 == 0

        for line in lines:
            text = line['text'][:line['chars_shown']]
            color = COLOR_RGB.get(line['type'], COLOR_RGB['bright_white'])
            if line['type'] == 'prompt':
                color = COLOR_RGB['prompt']
            elif line['type'] == 'comment':
                color = COLOR_RGB['comment']

            draw.text((50, y), text, font=renderer.font_code, fill=color)

            if cursor_on and line.get('active'):
                cursor_x = 50 + len(text) * 12
                draw.rectangle([(cursor_x, y), (cursor_x + 10, y + 24)], fill=COLOR_RGB['green'])

            y += line_height

        yield img


def generate_unit_circle_frames(renderer: StreamingRenderer, duration: float,
                                 fps: int) -> Generator[Image.Image, None, None]:
    """Generate unit circle with sine wave frames."""
    total_frames = int(duration * fps)

    # Scale positions based on resolution
    scale = min(renderer.width / 1920, renderer.height / 1080)
    circle_cx = int(400 * scale)
    circle_cy = int(500 * scale)
    circle_radius = int(200 * scale)
    wave_x = int(700 * scale)
    wave_y = int(500 * scale)
    wave_width = int(600 * scale)
    wave_height = int(400 * scale)

    for frame in range(total_frames):
        t = frame / fps
        theta = t * 1.5

        img, draw = renderer.new_frame()

        draw.text((50, 30), "Unit Circle & Trigonometry", font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        px, py = renderer.draw_unit_circle(draw, circle_cx, circle_cy, circle_radius, theta)

        cos_val = math.cos(theta)
        sin_val = math.sin(theta)
        draw.text((50, int(renderer.height * 0.74)),
                 f"P = (cos, sin) = ({cos_val:.3f}, {sin_val:.3f})",
                 font=renderer.font_medium, fill=COLOR_RGB['white'])

        draw.text((wave_x, int(renderer.height * 0.23)), "Sine Wave: y = sin(t)",
                 font=renderer.font_medium, fill=COLOR_RGB['cyan'])
        renderer.draw_sine_wave(draw, wave_x, wave_y, wave_width, wave_height, theta)

        # Connection line
        wave_y_point = wave_y - int(wave_height/2 * sin_val)
        draw.line([(px, py), (wave_x, wave_y_point)], fill=COLOR_RGB['yellow'], width=1)

        draw.text((50, int(renderer.height * 0.83)),
                 "x = cos(t)    y = sin(t)",
                 font=renderer.font_small, fill=COLOR_RGB['comment'])

        yield img


def generate_euler_frames(renderer: StreamingRenderer, duration: float,
                          fps: int) -> Generator[Image.Image, None, None]:
    """Generate Euler's formula frames."""
    total_frames = int(duration * fps)
    scale = min(renderer.width / 1920, renderer.height / 1080)

    plane_cx = renderer.width // 2
    plane_cy = int(550 * scale)
    plane_radius = int(250 * scale)

    for frame in range(total_frames):
        t = frame / fps
        theta = t * 1.2

        img, draw = renderer.new_frame()

        draw.text((50, 30), "Euler's Formula: Complex Numbers",
                 font=renderer.font_large, fill=COLOR_RGB['bright_white'])
        draw.text((renderer.width//2 - int(200*scale), int(120*scale)),
                 "e^(i*t) = cos(t) + i*sin(t)",
                 font=renderer.font_large, fill=COLOR_RGB['bright_yellow'])

        # Axes
        draw.line([(plane_cx - plane_radius - 50, plane_cy),
                  (plane_cx + plane_radius + 50, plane_cy)], fill=(60, 60, 80), width=2)
        draw.line([(plane_cx, plane_cy - plane_radius - 50),
                  (plane_cx, plane_cy + plane_radius + 50)], fill=(60, 60, 80), width=2)

        draw.text((plane_cx + plane_radius + 20, plane_cy - 15), "Real",
                 font=renderer.font_small, fill=COLOR_RGB['cyan'])
        draw.text((plane_cx + 10, plane_cy - plane_radius - 40), "Imag",
                 font=renderer.font_small, fill=COLOR_RGB['magenta'])

        # Circle
        draw.ellipse([(plane_cx - plane_radius, plane_cy - plane_radius),
                     (plane_cx + plane_radius, plane_cy + plane_radius)],
                    outline=COLOR_RGB['cyan'], width=2)

        # Point
        px = plane_cx + int(plane_radius * math.cos(theta))
        py = plane_cy - int(plane_radius * math.sin(theta))

        draw.line([(plane_cx, plane_cy), (px, py)], fill=COLOR_RGB['bright_green'], width=3)
        draw.line([(plane_cx, plane_cy), (px, plane_cy)], fill=COLOR_RGB['cyan'], width=2)
        draw.line([(px, plane_cy), (px, py)], fill=COLOR_RGB['magenta'], width=2)
        draw.ellipse([(px - 10, py - 10), (px + 10, py + 10)], fill=COLOR_RGB['bright_yellow'])

        cos_val = math.cos(theta)
        sin_val = math.sin(theta)
        draw.text((50, int(renderer.height * 0.78)),
                 f"e^(i*{math.degrees(theta):.0f}deg) = {cos_val:.3f} + i*{sin_val:.3f}",
                 font=renderer.font_medium, fill=COLOR_RGB['white'])

        yield img


def generate_lissajous_frames(renderer: StreamingRenderer, duration: float,
                               fps: int, freq_a: int = 3, freq_b: int = 2,
                               phase_offset: float = 0.0) -> Generator[Image.Image, None, None]:
    """Generate Lissajous connection frames with configurable frequencies."""
    total_frames = int(duration * fps)
    scale = min(renderer.width / 1920, renderer.height / 1080)

    # Positions - X circle on left, Y circle below it, result on right
    cx1, cy1, r1 = int(250*scale), int(350*scale), int(120*scale)
    cx2, cy2, r2 = int(250*scale), int(650*scale), int(120*scale)
    liss_cx, liss_cy = int(900*scale), int(500*scale)
    liss_scale = int(220*scale)

    for frame in range(total_frames):
        t = frame / fps

        img, draw = renderer.new_frame()

        # Title with ratio
        draw.text((50, 30), f"Lissajous Curve  {freq_a}:{freq_b}",
                 font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        # X circle (horizontal driver)
        theta_x = t * freq_a + phase_offset
        px1 = cx1 + int(r1 * math.cos(theta_x))
        py1 = cy1 - int(r1 * math.sin(theta_x))

        # Circle outline and center
        draw.ellipse([(cx1 - r1, cy1 - r1), (cx1 + r1, cy1 + r1)],
                    outline=COLOR_RGB['cyan'], width=2)
        draw.ellipse([(cx1 - 3, cy1 - 3), (cx1 + 3, cy1 + 3)], fill=COLOR_RGB['white'])

        # Radial line
        draw.line([(cx1, cy1), (px1, py1)], fill=COLOR_RGB['cyan'], width=2)

        # Point on X circle
        draw.ellipse([(px1 - 8, py1 - 8), (px1 + 8, py1 + 8)], fill=COLOR_RGB['cyan'])

        # Label
        draw.text((cx1 - 60, cy1 - r1 - 35), f"x = sin({freq_a}t)",
                 font=renderer.font_small, fill=COLOR_RGB['cyan'])

        # Y circle (vertical driver)
        theta_y = t * freq_b
        px2 = cx2 + int(r2 * math.cos(theta_y))
        py2 = cy2 - int(r2 * math.sin(theta_y))

        # Circle outline and center
        draw.ellipse([(cx2 - r2, cy2 - r2), (cx2 + r2, cy2 + r2)],
                    outline=COLOR_RGB['magenta'], width=2)
        draw.ellipse([(cx2 - 3, cy2 - 3), (cx2 + 3, cy2 + 3)], fill=COLOR_RGB['white'])

        # Radial line
        draw.line([(cx2, cy2), (px2, py2)], fill=COLOR_RGB['magenta'], width=2)

        # Point on Y circle
        draw.ellipse([(px2 - 8, py2 - 8), (px2 + 8, py2 + 8)], fill=COLOR_RGB['magenta'])

        # Label
        draw.text((cx2 - 60, cy2 - r2 - 35), f"y = sin({freq_b}t)",
                 font=renderer.font_small, fill=COLOR_RGB['magenta'])

        # Current Lissajous position
        curr_lx = liss_cx + int(liss_scale * math.sin(freq_a * t + phase_offset))
        curr_ly = liss_cy - int(liss_scale * math.sin(freq_b * t))

        # Connection lines from circles to Lissajous point
        # Horizontal line from X circle point
        draw.line([(px1, py1), (px1, cy1)], fill=(60, 60, 80), width=1)
        draw.line([(px1, cy1), (curr_lx, cy1)], fill=COLOR_RGB['cyan'], width=1)
        draw.line([(curr_lx, cy1), (curr_lx, curr_ly)], fill=(60, 60, 80), width=1)

        # Vertical line from Y circle point
        draw.line([(px2, py2), (cx2, py2)], fill=(60, 60, 80), width=1)

        # Lissajous trail with gradient
        trail_points = []
        for i in range(300):
            trail_t = t - i * 0.015
            if trail_t < 0:
                continue
            lx = liss_cx + int(liss_scale * math.sin(freq_a * trail_t + phase_offset))
            ly = liss_cy - int(liss_scale * math.sin(freq_b * trail_t))
            trail_points.append((lx, ly, i))

        # Draw trail from oldest to newest
        for lx, ly, i in reversed(trail_points):
            alpha = 1.0 - i / 300
            size = int(2 + alpha * 6)
            if alpha > 0.85:
                color = COLOR_RGB['bright_white']
            elif alpha > 0.6:
                color = COLOR_RGB['bright_green']
            elif alpha > 0.3:
                color = COLOR_RGB['green']
            else:
                color = (50, 80, 50)
            draw.ellipse([(lx - size//2, ly - size//2), (lx + size//2, ly + size//2)], fill=color)

        # Current point (bright)
        draw.ellipse([(curr_lx - 12, curr_ly - 12), (curr_lx + 12, curr_ly + 12)],
                    fill=COLOR_RGB['bright_yellow'])

        # Ratio label below curve
        draw.text((liss_cx - 80, liss_cy + liss_scale + 40),
                 f"Ratio {freq_a}:{freq_b}",
                 font=renderer.font_medium, fill=COLOR_RGB['yellow'])

        # Time display
        draw.text((renderer.width - 150, renderer.height - 40),
                 f"t = {t:.1f}s",
                 font=renderer.font_small, fill=COLOR_RGB['comment'])

        yield img


def generate_lissajous_gallery(renderer: StreamingRenderer, duration: float,
                                fps: int) -> Generator[Image.Image, None, None]:
    """Generate a gallery showing multiple Lissajous patterns simultaneously."""
    total_frames = int(duration * fps)
    scale = min(renderer.width / 1920, renderer.height / 1080)

    # Different ratios to show
    patterns = [
        (1, 2, 'Simple'),
        (2, 3, 'Musical'),
        (3, 4, 'Complex'),
        (3, 5, 'Elegant'),
        (4, 5, 'Intricate'),
        (5, 6, 'Dense'),
    ]

    # Grid layout: 3 columns x 2 rows
    cols, rows = 3, 2
    cell_w = renderer.width // cols
    cell_h = (renderer.height - 80) // rows  # Leave space for title

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Title
        draw.text((50, 20), "Lissajous Pattern Gallery",
                 font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        for idx, (freq_a, freq_b, name) in enumerate(patterns):
            col = idx % cols
            row = idx // cols

            # Cell center
            cx = col * cell_w + cell_w // 2
            cy = 80 + row * cell_h + cell_h // 2
            pattern_scale = int(min(cell_w, cell_h) * 0.35)

            # Draw mini Lissajous
            trail_len = 200
            for i in range(trail_len):
                trail_t = t - i * 0.02
                if trail_t < 0:
                    continue
                lx = cx + int(pattern_scale * math.sin(freq_a * trail_t))
                ly = cy - int(pattern_scale * math.sin(freq_b * trail_t))
                alpha = 1.0 - i / trail_len
                size = int(2 + alpha * 4)
                if alpha > 0.8:
                    color = COLOR_RGB['bright_cyan']
                elif alpha > 0.5:
                    color = COLOR_RGB['cyan']
                else:
                    color = (60, 100, 110)
                draw.ellipse([(lx - size//2, ly - size//2), (lx + size//2, ly + size//2)], fill=color)

            # Current point
            curr_x = cx + int(pattern_scale * math.sin(freq_a * t))
            curr_y = cy - int(pattern_scale * math.sin(freq_b * t))
            draw.ellipse([(curr_x - 6, curr_y - 6), (curr_x + 6, curr_y + 6)],
                        fill=COLOR_RGB['bright_yellow'])

            # Label
            draw.text((cx - 40, cy + pattern_scale + 10),
                     f"{freq_a}:{freq_b}",
                     font=renderer.font_medium, fill=COLOR_RGB['yellow'])

        yield img


def render_to_video(output_path: str, width: int, height: int, fps: int,
                    frame_generator, total_frames: int):
    """Render frames to video using temp files (more Windows-compatible)."""
    import tempfile
    import shutil

    # Find ffmpeg
    ffmpeg_cmd = 'ffmpeg'
    if platform.system() == 'Windows':
        scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
        if os.path.exists(scoop_ffmpeg):
            ffmpeg_cmd = scoop_ffmpeg

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='unit_circle_')

    print(f"Rendering: {width}x{height} @ {fps}fps")
    print(f"Total frames: {total_frames}")
    print(f"Temp dir: {temp_dir}")
    print(f"Output: {output_path}")
    print()

    try:
        # Render frames to files
        for i, frame in enumerate(frame_generator):
            frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
            frame.save(frame_path, optimize=False)

            if (i + 1) % 50 == 0:
                pct = (i + 1) / total_frames * 100
                print(f"  Frame {i + 1}/{total_frames} ({pct:.1f}%)")

        print(f"\nFrames complete. Encoding with ffmpeg...")

        # Encode with ffmpeg
        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')
        cmd = [
            ffmpeg_cmd, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '20',
            '-preset', 'fast',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size = os.path.getsize(output_path) / 1024 / 1024
            print(f"\nSuccess! {output_path}")
            print(f"Size: {size:.1f} MB")
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg.")
        print("  Windows: scoop install ffmpeg")
        return False
    finally:
        # Cleanup temp files
        print(f"Cleaning up temp files...")
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_unit_circle_stream(output_path: str = None, preview: bool = False):
    """Render the complete educational video using streaming."""

    # Resolution settings - focused on Lissajous patterns
    if preview:
        width, height, fps = 1280, 720, 15
        durations = {
            'intro': 4,
            'euler': 12,
            'liss_3_2': 10,   # Classic 3:2
            'liss_2_3': 8,    # 2:3 variant
            'liss_3_4': 8,    # 3:4
            'liss_5_4': 8,    # 5:4
            'gallery': 10,   # Show multiple at once
            'outro': 5
        }
    else:
        width, height, fps = 1920, 1080, 30
        durations = {
            'intro': 6,
            'euler': 20,
            'liss_3_2': 15,
            'liss_2_3': 12,
            'liss_3_4': 12,
            'liss_5_4': 12,
            'gallery': 15,
            'outro': 6
        }

    if output_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_path = os.path.join(base_dir, 'unit-circle-educational.mp4')

    renderer = StreamingRenderer(width, height)

    # Calculate total frames
    total_frames = sum(int(d * fps) for d in durations.values())

    print("=" * 60)
    print("Lissajous Curves Educational Video")
    print("=" * 60)
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Total duration: {total_frames / fps:.1f}s")
    print()

    def combined_generator():
        # Segment 1: Intro
        print("Segment 1: Ghost typing intro...")
        intro_commands = [
            "$ cd atari-style",
            "$ python -m atari_style.demos.lissajous",
            "# Exploring parametric curves...",
            "# x = sin(a*t), y = sin(b*t)",
        ]
        yield from generate_ghost_typing_frames(renderer, intro_commands, durations['intro'], fps)

        # Segment 2: Euler's formula (good section)
        print("Segment 2: Euler's formula...")
        yield from generate_euler_frames(renderer, durations['euler'], fps)

        # Segment 3: Lissajous 3:2 (classic)
        print("Segment 3: Lissajous 3:2...")
        yield from generate_lissajous_frames(renderer, durations['liss_3_2'], fps, freq_a=3, freq_b=2)

        # Segment 4: Lissajous 2:3
        print("Segment 4: Lissajous 2:3...")
        yield from generate_lissajous_frames(renderer, durations['liss_2_3'], fps, freq_a=2, freq_b=3)

        # Segment 5: Lissajous 3:4
        print("Segment 5: Lissajous 3:4...")
        yield from generate_lissajous_frames(renderer, durations['liss_3_4'], fps, freq_a=3, freq_b=4)

        # Segment 6: Lissajous 5:4
        print("Segment 6: Lissajous 5:4...")
        yield from generate_lissajous_frames(renderer, durations['liss_5_4'], fps, freq_a=5, freq_b=4)

        # Segment 7: Gallery
        print("Segment 7: Pattern gallery...")
        yield from generate_lissajous_gallery(renderer, durations['gallery'], fps)

        # Segment 8: Outro
        print("Segment 8: Ghost typing outro...")
        outro_commands = [
            "# Parametric beauty!",
            "$ # x = sin(a*t), y = sin(b*t)",
            "$ # Different ratios = different patterns",
            "$ # github.com/jcaldwell-labs/atari-style",
        ]
        yield from generate_ghost_typing_frames(renderer, outro_commands, durations['outro'], fps)

    return render_to_video(output_path, width, height, fps, combined_generator(), total_frames)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Render Unit Circle Educational Video')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--preview', '-p', action='store_true',
                       help='Preview mode (720p, 15fps, shorter)')

    args = parser.parse_args()

    success = render_unit_circle_stream(args.output, args.preview)
    sys.exit(0 if success else 1)
