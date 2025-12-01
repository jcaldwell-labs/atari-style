"""Unit Circle Educational Demo - Trigonometry visualization.

Shows the connection between:
- Unit circle rotation
- Sine/cosine wave generation
- Complex numbers (Euler's formula)
- Lissajous curves

Features ghost typing intro/outro for meta presentation.
"""

import os
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
from ..core.renderer import Color


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


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Bresenham's line algorithm - returns list of (x, y) points."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    if dx > dy:
        err = dx / 2
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy

    points.append((x1, y1))
    return points


class EducationalRenderer:
    """Renders educational content with text overlays."""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.bg_color = (30, 32, 44)

        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
            self.font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
        except:
            self.font_large = ImageFont.load_default()
            self.font_medium = self.font_large
            self.font_small = self.font_large
            self.font_code = self.font_large

    def new_frame(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        return img, ImageDraw.Draw(img)

    def draw_unit_circle(self, draw: ImageDraw.Draw, cx: int, cy: int, radius: int,
                        theta: float, show_radial: bool = True, show_coords: bool = True):
        """Draw unit circle with rotating point and optional radial."""

        # Draw axes
        draw.line([(cx - radius - 20, cy), (cx + radius + 20, cy)], fill=(60, 60, 80), width=1)
        draw.line([(cx, cy - radius - 20), (cx, cy + radius + 20)], fill=(60, 60, 80), width=1)

        # Draw circle
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                    outline=COLOR_RGB['cyan'], width=2)

        # Calculate point position
        px = cx + int(radius * math.cos(theta))
        py = cy - int(radius * math.sin(theta))  # Negative because y is inverted

        # Draw radial line (Bresenham)
        if show_radial:
            points = bresenham_line(cx, cy, px, py)
            for i, (x, y) in enumerate(points):
                # Gradient from center to edge
                intensity = i / len(points)
                char_size = 3 + int(intensity * 4)
                color = COLOR_RGB['bright_green'] if intensity > 0.8 else COLOR_RGB['green']
                draw.ellipse([(x - char_size//2, y - char_size//2),
                             (x + char_size//2, y + char_size//2)], fill=color)

        # Draw point P
        draw.ellipse([(px - 8, py - 8), (px + 8, py + 8)], fill=COLOR_RGB['bright_yellow'])

        # Draw center
        draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=COLOR_RGB['white'])

        # Draw projection lines (to show cos and sin)
        if show_coords:
            # Vertical line (sin)
            draw.line([(px, cy), (px, py)], fill=COLOR_RGB['magenta'], width=2)
            # Horizontal line (cos)
            draw.line([(cx, py), (px, py)], fill=COLOR_RGB['cyan'], width=2)

            # Labels
            draw.text((px + 10, (cy + py) // 2), "sin θ", font=self.font_small, fill=COLOR_RGB['magenta'])
            draw.text(((cx + px) // 2, py + 10), "cos θ", font=self.font_small, fill=COLOR_RGB['cyan'])

        # Angle label
        draw.text((cx + 15, cy + 15), f"θ = {math.degrees(theta):.0f}°", font=self.font_medium, fill=COLOR_RGB['yellow'])

        return px, py

    def draw_sine_wave(self, draw: ImageDraw.Draw, x_start: int, y_center: int,
                      width: int, height: int, phase: float, frequency: float = 1.0,
                      amplitude: float = 1.0, highlight_x: float = None):
        """Draw sine wave with optional highlight point."""

        # Draw axis
        draw.line([(x_start, y_center), (x_start + width, y_center)], fill=(60, 60, 80), width=1)

        # Draw wave
        prev_point = None
        points = []
        for x in range(width):
            t = (x / width) * 2 * math.pi * frequency
            y = y_center - int(height/2 * amplitude * math.sin(t + phase))
            points.append((x_start + x, y))

            if prev_point:
                draw.line([prev_point, (x_start + x, y)], fill=COLOR_RGB['cyan'], width=2)
            prev_point = (x_start + x, y)

        # Highlight current phase position
        if highlight_x is not None:
            hx = x_start + int((phase % (2 * math.pi)) / (2 * math.pi * frequency) * width)
            hx = hx % (x_start + width)
            if x_start <= hx < x_start + width:
                hy = y_center - int(height/2 * amplitude * math.sin(phase))
                draw.ellipse([(hx - 6, hy - 6), (hx + 6, hy + 6)], fill=COLOR_RGB['bright_yellow'])

        return points

    def draw_ghost_typing(self, draw: ImageDraw.Draw, lines: List[dict], cursor_visible: bool = True):
        """Draw terminal with ghost typing effect.

        lines: list of {'text': str, 'chars_shown': int, 'type': 'prompt'|'command'|'comment'|'output'}
        """
        y = 100
        line_height = 30

        for line in lines:
            text = line['text'][:line.get('chars_shown', len(line['text']))]
            line_type = line.get('type', 'command')

            if line_type == 'prompt':
                color = COLOR_RGB['prompt']
            elif line_type == 'comment':
                color = COLOR_RGB['comment']
            elif line_type == 'output':
                color = COLOR_RGB['white']
            else:
                color = COLOR_RGB['bright_white']

            draw.text((50, y), text, font=self.font_code, fill=color)

            # Cursor on active line
            if cursor_visible and line.get('active', False):
                cursor_x = 50 + len(text) * 12  # Approximate char width
                draw.rectangle([(cursor_x, y), (cursor_x + 10, y + 24)], fill=COLOR_RGB['green'])

            y += line_height


def render_ghost_typing_segment(renderer: EducationalRenderer, commands: List[str],
                                duration: float, fps: int = 30) -> List[Image.Image]:
    """Render ghost typing segment."""
    frames = []
    total_frames = int(duration * fps)

    # Calculate typing speed (chars per frame)
    total_chars = sum(len(cmd) for cmd in commands)
    chars_per_second = total_chars / (duration * 0.7)  # Leave 30% for pauses

    lines = []
    for cmd in commands:
        if cmd.startswith('#'):
            lines.append({'text': cmd, 'chars_shown': 0, 'type': 'comment', 'active': False})
        elif cmd.startswith('$'):
            lines.append({'text': cmd, 'chars_shown': 0, 'type': 'prompt', 'active': False})
        else:
            lines.append({'text': cmd, 'chars_shown': 0, 'type': 'command', 'active': False})

    current_line = 0
    char_accumulator = 0.0

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Update typing progress
        if current_line < len(lines):
            lines[current_line]['active'] = True
            char_accumulator += chars_per_second / fps

            while char_accumulator >= 1 and current_line < len(lines):
                if lines[current_line]['chars_shown'] < len(lines[current_line]['text']):
                    lines[current_line]['chars_shown'] += 1
                    char_accumulator -= 1
                else:
                    lines[current_line]['active'] = False
                    current_line += 1
                    if current_line < len(lines):
                        lines[current_line]['active'] = True
                    char_accumulator = 0
                    break

        # Draw terminal
        cursor_visible = (frame // 15) % 2 == 0  # Blink cursor
        renderer.draw_ghost_typing(draw, lines, cursor_visible)

        frames.append(img)

    return frames


def render_unit_circle_segment(renderer: EducationalRenderer, duration: float,
                               fps: int = 30, show_wave: bool = True) -> List[Image.Image]:
    """Render unit circle with sine wave extraction."""
    frames = []
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        theta = t * 1.5  # Rotation speed

        img, draw = renderer.new_frame()

        # Title
        draw.text((50, 30), "Unit Circle & Trigonometry", font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        # Unit circle (left side)
        circle_cx = 400
        circle_cy = 500
        circle_radius = 200

        px, py = renderer.draw_unit_circle(draw, circle_cx, circle_cy, circle_radius, theta)

        # Coordinate display
        cos_val = math.cos(theta)
        sin_val = math.sin(theta)
        draw.text((50, 800), f"P = (cos θ, sin θ) = ({cos_val:.3f}, {sin_val:.3f})",
                 font=renderer.font_medium, fill=COLOR_RGB['white'])

        # Sine wave (right side)
        if show_wave:
            wave_x = 700
            wave_y = 500
            wave_width = 600
            wave_height = 400

            draw.text((wave_x, 250), "Sine Wave: y = sin(θ)", font=renderer.font_medium, fill=COLOR_RGB['cyan'])
            renderer.draw_sine_wave(draw, wave_x, wave_y, wave_width, wave_height,
                                   theta, frequency=1.0, amplitude=1.0, highlight_x=theta)

            # Connection line from circle to wave
            wave_current_x = wave_x
            wave_current_y = wave_y - int(wave_height/2 * sin_val)
            draw.line([(px, py), (wave_current_x, wave_current_y)],
                     fill=COLOR_RGB['yellow'], width=1)

        # Formula
        draw.text((50, 900), "x = cos(θ)    y = sin(θ)    θ = angle from positive x-axis",
                 font=renderer.font_small, fill=COLOR_RGB['comment'])

        frames.append(img)

    return frames


def render_euler_segment(renderer: EducationalRenderer, duration: float,
                        fps: int = 30) -> List[Image.Image]:
    """Render Euler's formula visualization."""
    frames = []
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        theta = t * 1.2

        img, draw = renderer.new_frame()

        # Title
        draw.text((50, 30), "Euler's Formula: Complex Numbers", font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        # The formula
        draw.text((renderer.width//2 - 200, 120), "e^(iθ) = cos(θ) + i·sin(θ)",
                 font=renderer.font_large, fill=COLOR_RGB['bright_yellow'])

        # Complex plane
        plane_cx = renderer.width // 2
        plane_cy = 550
        plane_radius = 250

        # Draw axes with labels
        draw.line([(plane_cx - plane_radius - 50, plane_cy), (plane_cx + plane_radius + 50, plane_cy)],
                 fill=(60, 60, 80), width=2)
        draw.line([(plane_cx, plane_cy - plane_radius - 50), (plane_cx, plane_cy + plane_radius + 50)],
                 fill=(60, 60, 80), width=2)

        draw.text((plane_cx + plane_radius + 20, plane_cy - 15), "Real", font=renderer.font_small, fill=COLOR_RGB['cyan'])
        draw.text((plane_cx + 10, plane_cy - plane_radius - 40), "Imaginary", font=renderer.font_small, fill=COLOR_RGB['magenta'])

        # Draw unit circle
        draw.ellipse([(plane_cx - plane_radius, plane_cy - plane_radius),
                     (plane_cx + plane_radius, plane_cy + plane_radius)],
                    outline=COLOR_RGB['cyan'], width=2)

        # Point on circle
        px = plane_cx + int(plane_radius * math.cos(theta))
        py = plane_cy - int(plane_radius * math.sin(theta))

        # Radial
        draw.line([(plane_cx, plane_cy), (px, py)], fill=COLOR_RGB['bright_green'], width=3)

        # Projections
        draw.line([(plane_cx, plane_cy), (px, plane_cy)], fill=COLOR_RGB['cyan'], width=2)  # Real part
        draw.line([(px, plane_cy), (px, py)], fill=COLOR_RGB['magenta'], width=2)  # Imaginary part

        # Point
        draw.ellipse([(px - 10, py - 10), (px + 10, py + 10)], fill=COLOR_RGB['bright_yellow'])

        # Labels
        cos_val = math.cos(theta)
        sin_val = math.sin(theta)
        draw.text((50, 850), f"e^(i·{math.degrees(theta):.0f}°) = {cos_val:.3f} + i·{sin_val:.3f}",
                 font=renderer.font_medium, fill=COLOR_RGB['white'])
        draw.text((50, 900), "Real part = cos(θ)     Imaginary part = sin(θ)",
                 font=renderer.font_small, fill=COLOR_RGB['comment'])

        frames.append(img)

    return frames


def render_lissajous_connection_segment(renderer: EducationalRenderer, duration: float,
                                        fps: int = 30) -> List[Image.Image]:
    """Show how two unit circles create Lissajous curves."""
    frames = []
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        freq_a = 3
        freq_b = 2

        img, draw = renderer.new_frame()

        # Title
        draw.text((50, 30), "Two Circles → Lissajous Curve", font=renderer.font_large, fill=COLOR_RGB['bright_white'])

        # X circle (top)
        cx1, cy1, r1 = 300, 300, 150
        theta_x = t * freq_a
        px1 = cx1 + int(r1 * math.cos(theta_x))
        py1 = cy1 - int(r1 * math.sin(theta_x))

        draw.text((cx1 - 50, cy1 - r1 - 40), f"x = cos({freq_a}t)", font=renderer.font_small, fill=COLOR_RGB['cyan'])
        draw.ellipse([(cx1 - r1, cy1 - r1), (cx1 + r1, cy1 + r1)], outline=COLOR_RGB['cyan'], width=2)
        draw.ellipse([(px1 - 6, py1 - 6), (px1 + 6, py1 + 6)], fill=COLOR_RGB['cyan'])

        # Y circle (left)
        cx2, cy2, r2 = 300, 700, 150
        theta_y = t * freq_b
        px2 = cx2 + int(r2 * math.cos(theta_y))
        py2 = cy2 - int(r2 * math.sin(theta_y))

        draw.text((cx2 - 50, cy2 - r2 - 40), f"y = sin({freq_b}t)", font=renderer.font_small, fill=COLOR_RGB['magenta'])
        draw.ellipse([(cx2 - r2, cy2 - r2), (cx2 + r2, cy2 + r2)], outline=COLOR_RGB['magenta'], width=2)
        draw.ellipse([(px2 - 6, py2 - 6), (px2 + 6, py2 + 6)], fill=COLOR_RGB['magenta'])

        # Lissajous result (right)
        liss_cx, liss_cy = 1000, 500
        liss_scale = 250

        # Draw Lissajous trail
        for i in range(200):
            trail_t = t - i * 0.02
            if trail_t < 0:
                continue
            lx = liss_cx + int(liss_scale * math.sin(freq_a * trail_t))
            ly = liss_cy - int(liss_scale * math.sin(freq_b * trail_t))
            alpha = 1.0 - i / 200
            size = int(3 + alpha * 5)
            if alpha > 0.8:
                color = COLOR_RGB['bright_white']
            elif alpha > 0.5:
                color = COLOR_RGB['bright_green']
            else:
                color = COLOR_RGB['green']
            draw.ellipse([(lx - size//2, ly - size//2), (lx + size//2, ly + size//2)], fill=color)

        # Current point
        curr_lx = liss_cx + int(liss_scale * math.sin(freq_a * t))
        curr_ly = liss_cy - int(liss_scale * math.sin(freq_b * t))
        draw.ellipse([(curr_lx - 10, curr_ly - 10), (curr_lx + 10, curr_ly + 10)], fill=COLOR_RGB['bright_yellow'])

        # Connection lines
        draw.line([(px1, cy1), (curr_lx, cy1)], fill=(60, 60, 80), width=1)
        draw.line([(curr_lx, cy1), (curr_lx, curr_ly)], fill=(60, 60, 80), width=1)

        # Label
        draw.text((liss_cx - 100, liss_cy + liss_scale + 30), f"Lissajous {freq_a}:{freq_b}",
                 font=renderer.font_medium, fill=COLOR_RGB['yellow'])

        frames.append(img)

    return frames


def _save_segment_frames(frames: List[Image.Image], frames_dir: str, start_index: int) -> int:
    """Save frames to disk immediately and return next index. Frees memory."""
    for i, frame in enumerate(frames):
        frame_path = os.path.join(frames_dir, f"frame_{start_index + i:05d}.png")
        frame.save(frame_path)
    return start_index + len(frames)


def render_unit_circle_educational(duration: int = 120, output_path: str = None):
    """Render complete educational video."""
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/unit-circle-educational.mp4"

    frames_dir = "/tmp/edu_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = EducationalRenderer()
    fps = 30
    frame_index = 0

    print("Rendering Unit Circle Educational Video")
    print("=" * 50)

    # Segment 1: Ghost typing intro (8 seconds)
    print("Segment 1: Ghost typing intro...")
    intro_commands = [
        "$ cd atari-style",
        "$ source venv/bin/activate",
        "$ python -m atari_style.demos.unit_circle",
        "# Starting unit circle visualization...",
    ]
    frames = render_ghost_typing_segment(renderer, intro_commands, 8, fps)
    frame_index = _save_segment_frames(frames, frames_dir, frame_index)
    print(f"  Saved {frame_index} frames")
    del frames  # Free memory

    # Segment 2: Unit circle basics (30 seconds)
    print("Segment 2: Unit circle basics...")
    frames = render_unit_circle_segment(renderer, 30, fps, show_wave=True)
    frame_index = _save_segment_frames(frames, frames_dir, frame_index)
    print(f"  Saved {frame_index} frames total")
    del frames

    # Segment 3: Euler's formula (25 seconds)
    print("Segment 3: Euler's formula...")
    frames = render_euler_segment(renderer, 25, fps)
    frame_index = _save_segment_frames(frames, frames_dir, frame_index)
    print(f"  Saved {frame_index} frames total")
    del frames

    # Segment 4: Lissajous connection (25 seconds)
    print("Segment 4: Lissajous connection...")
    frames = render_lissajous_connection_segment(renderer, 25, fps)
    frame_index = _save_segment_frames(frames, frames_dir, frame_index)
    print(f"  Saved {frame_index} frames total")
    del frames

    # Segment 5: Ghost typing outro (10 seconds)
    print("Segment 5: Ghost typing outro...")
    outro_commands = [
        "# Render complete!",
        "$ # The mathematics of motion:",
        "$ # x = cos(θ), y = sin(θ)",
        "$ # e^(iθ) = cos(θ) + i·sin(θ)",
        "$ # github.com/jcaldwell-labs/atari-style",
    ]
    frames = render_ghost_typing_segment(renderer, outro_commands, 10, fps)
    frame_index = _save_segment_frames(frames, frames_dir, frame_index)
    print(f"  Saved {frame_index} frames total")
    del frames

    total_frames = frame_index
    print(f"\nAll {total_frames} frames saved to disk")

    # Create video
    print("\nCreating video with ffmpeg...")
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
        duration_actual = total_frames / fps
        print(f"\nSuccess! {output_path}")
        print(f"Duration: {duration_actual:.1f}s | Size: {size / 1024 / 1024:.1f} MB")

        # Cleanup
        for f in os.listdir(frames_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(frames_dir, f))
        return True
    else:
        print(f"Error: {result.stderr}")
        return False


if __name__ == "__main__":
    render_unit_circle_educational()
