"""Gimbal Renderer - Rotating interlocked rings with field modulation.

Pièce de résistance animation featuring:
- Multiple Lissajous circles (a=b) appearing to rotate in 3D
- Gimbal-like interlocking rings at different orientations
- Height field from wave interference driving ring properties
- Parametric exploration as the field evolves
"""

import os
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
from ..core.renderer import Color


# Cosmic palette - ethereal blues, cyans, and whites
COSMIC = [
    Color.BLUE, Color.BLUE, Color.CYAN,
    Color.BRIGHT_CYAN, Color.BRIGHT_CYAN,
    Color.WHITE, Color.BRIGHT_WHITE,
]

# Aurora palette - greens and magentas
AURORA = [
    Color.GREEN, Color.BRIGHT_GREEN,
    Color.CYAN, Color.BRIGHT_CYAN,
    Color.MAGENTA, Color.BRIGHT_MAGENTA,
    Color.BRIGHT_WHITE,
]

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


class MockRenderer:
    def __init__(self, width: int = 120, height: int = 40):
        self.width = width
        self.height = height
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.color_buffer = [[None for _ in range(width)] for _ in range(height)]
        # Depth buffer for 3D layering
        self.depth_buffer = [[float('inf') for _ in range(width)] for _ in range(height)]

    def clear_buffer(self):
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = ' '
                self.color_buffer[y][x] = None
                self.depth_buffer[y][x] = float('inf')

    def set_pixel_3d(self, x: int, y: int, z: float, char: str, color):
        """Set pixel with depth testing."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if z < self.depth_buffer[y][x]:
                self.buffer[y][x] = char[0] if char else ' '
                self.color_buffer[y][x] = color
                self.depth_buffer[y][x] = z


class GimbalRenderer:
    def __init__(self, width: int = 120, height: int = 40, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cell_width = 14
        self.cell_height = 26
        self.img_width = width * self.cell_width
        self.img_height = height * self.cell_height
        self.mock_renderer = MockRenderer(width, height)
        self.bg_color = (15, 20, 35)  # Deep space blue

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


def compute_height_field(x: int, y: int, t: float, width: int, height: int) -> float:
    """Compute interference pattern height at position."""
    cx, cy = width / 2, height / 2
    dx, dy = x - cx, y - cy
    r = math.sqrt(dx*dx + dy*dy)

    # Multiple wave sources
    wave1 = math.sin(r * 0.15 - t * 2)
    wave2 = math.sin(dx * 0.1 + t * 1.5) * math.cos(dy * 0.1)
    wave3 = math.cos(r * 0.08 + t * 0.8) * 0.5

    return (wave1 + wave2 + wave3) / 2.5


def render_gimbal_rings(duration: int = 45, output_path: str = None):
    """Render gimbal-like rotating rings with field modulation.

    Creates 3 interlocked rings (like a gyroscope) that rotate
    independently, with their appearance modulated by a wave field.
    """
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/gimbal-rings.mp4"

    frames_dir = "/tmp/gimbal_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = GimbalRenderer(width=120, height=40, fps=30)
    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering GIMBAL RINGS: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    cx = renderer.width // 2
    cy = renderer.height // 2

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        # Three gimbal rings with different rotation axes
        rings = [
            # (tilt_x, tilt_y, rotation_speed, radius, color_offset)
            (0.0, 0.0, 1.0, 18, 0),        # XY plane ring
            (math.pi/2, 0.0, 0.7, 16, 2),  # XZ plane ring
            (0.0, math.pi/2, 0.5, 14, 4),  # YZ plane ring
        ]

        for tilt_x, tilt_y, rot_speed, radius, color_off in rings:
            # Rotation angle for this ring
            rotation = t * rot_speed

            # Add breathing effect
            r_mod = radius + 2 * math.sin(t * 0.5 + color_off)

            # Draw ring as series of points
            for i in range(120):
                angle = (i / 120) * 2 * math.pi

                # Start with circle in XY plane
                px = r_mod * math.cos(angle + rotation)
                py = r_mod * math.sin(angle + rotation)
                pz = 0

                # Apply tilt rotations (gimbal axes)
                # Rotate around X axis
                py2 = py * math.cos(tilt_x) - pz * math.sin(tilt_x)
                pz2 = py * math.sin(tilt_x) + pz * math.cos(tilt_x)
                py, pz = py2, pz2

                # Rotate around Y axis
                px2 = px * math.cos(tilt_y) + pz * math.sin(tilt_y)
                pz2 = -px * math.sin(tilt_y) + pz * math.cos(tilt_y)
                px, pz = px2, pz2

                # Add slow precession
                prec = t * 0.3
                px3 = px * math.cos(prec) - py * math.sin(prec)
                py3 = px * math.sin(prec) + py * math.cos(prec)
                px, py = px3, py3

                # Project to screen (aspect ratio correction)
                screen_x = int(cx + px * 2.2)
                screen_y = int(cy + py * 0.55)

                if not (0 <= screen_x < renderer.width and 0 <= screen_y < renderer.height):
                    continue

                # Get height field modulation at this point
                field = compute_height_field(screen_x, screen_y, t, renderer.width, renderer.height)

                # Modulate character based on field and depth
                depth_factor = (pz + 20) / 40  # Normalize depth to 0-1
                intensity = (field + 1) / 2 * depth_factor

                if intensity < 0.2:
                    char = '·'
                    color_idx = 0
                elif intensity < 0.4:
                    char = '∘'
                    color_idx = 1
                elif intensity < 0.6:
                    char = '○'
                    color_idx = 2
                elif intensity < 0.8:
                    char = '●'
                    color_idx = 3
                else:
                    char = '◉'
                    color_idx = 4

                color_idx = (color_idx + color_off) % len(COSMIC)
                renderer.mock_renderer.set_pixel_3d(screen_x, screen_y, pz, char, COSMIC[color_idx])

        # Add field visualization as subtle background
        for y in range(renderer.height):
            for x in range(renderer.width):
                if renderer.mock_renderer.buffer[y][x] != ' ':
                    continue

                field = compute_height_field(x, y, t, renderer.width, renderer.height)
                if abs(field) > 0.7:
                    renderer.mock_renderer.buffer[y][x] = '·'
                    renderer.mock_renderer.color_buffer[y][x] = COSMIC[0]

        img = renderer.render_frame()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 200 == 0:
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


def render_field_circles(duration: int = 45, output_path: str = None):
    """Render concentric circles driven by height field.

    Multiple Lissajous circles (a=b) at different radii,
    with rotation and size modulated by interference pattern.
    """
    if output_path is None:
        output_path = "/home/be-dev-agent/projects/jcaldwell-labs/media/output/field-circles.mp4"

    frames_dir = "/tmp/gimbal_frames"
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(frames_dir, f))

    renderer = GimbalRenderer(width=120, height=40, fps=30)
    fps = renderer.fps
    total_frames = duration * fps

    print(f"Rendering FIELD CIRCLES: {total_frames} frames")
    print(f"Output: {output_path}")
    print()

    start_time = time.time()

    cx = renderer.width // 2
    cy = renderer.height // 2

    for frame_num in range(total_frames):
        t = frame_num / fps
        renderer.mock_renderer.clear_buffer()

        # Draw subtle field background first
        for y in range(renderer.height):
            for x in range(renderer.width):
                field = compute_height_field(x, y, t, renderer.width, renderer.height)
                if abs(field) > 0.6:
                    renderer.mock_renderer.buffer[y][x] = '·'
                    idx = int((field + 1) / 2 * (len(AURORA) - 1))
                    renderer.mock_renderer.color_buffer[y][x] = AURORA[min(idx, len(AURORA)-1)]

        # Concentric circles with field-driven modulation
        num_circles = 8
        for ring in range(num_circles):
            base_radius = 4 + ring * 2.5

            # Each ring rotates at different speed
            rotation = t * (0.5 + ring * 0.15) * (1 if ring % 2 == 0 else -1)

            # Sample field at multiple points on ring for modulation
            field_samples = []
            for sample in range(8):
                sample_angle = sample * math.pi / 4
                sx = int(cx + base_radius * 2 * math.cos(sample_angle))
                sy = int(cy + base_radius * 0.5 * math.sin(sample_angle))
                if 0 <= sx < renderer.width and 0 <= sy < renderer.height:
                    field_samples.append(compute_height_field(sx, sy, t, renderer.width, renderer.height))

            avg_field = sum(field_samples) / len(field_samples) if field_samples else 0

            # Field modulates radius and brightness
            radius_mod = base_radius * (1 + 0.2 * avg_field)

            # Draw circle points
            for i in range(80):
                angle = (i / 80) * 2 * math.pi + rotation

                # Lissajous with a=b=1 creates circle
                x = int(cx + radius_mod * math.cos(angle) * 2.2)  # Aspect correction
                y = int(cy + radius_mod * math.sin(angle) * 0.55)

                if not (0 <= x < renderer.width and 0 <= y < renderer.height):
                    continue

                # Local field modulation
                local_field = compute_height_field(x, y, t, renderer.width, renderer.height)

                # Choose character based on field intensity
                intensity = (local_field + 1) / 2
                if intensity < 0.25:
                    char = '·'
                elif intensity < 0.5:
                    char = '○'
                elif intensity < 0.75:
                    char = '●'
                else:
                    char = '◉'

                # Color based on ring index and field
                color_idx = (ring + int(intensity * 3)) % len(AURORA)
                renderer.mock_renderer.buffer[y][x] = char
                renderer.mock_renderer.color_buffer[y][x] = AURORA[color_idx]

        img = renderer.render_frame()
        frame_path = os.path.join(frames_dir, f"frame_{frame_num:05d}.png")
        img.save(frame_path)

        if (frame_num + 1) % 200 == 0:
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


def render_all_gimbal(duration: int = 45):
    """Render all gimbal animations."""
    print("=" * 60)
    print("PIECE DE RESISTANCE: GIMBAL ANIMATIONS")
    print("=" * 60)
    print()

    render_gimbal_rings(duration)
    print()
    render_field_circles(duration)

    print("\n" + "=" * 60)
    print("ALL GIMBAL RENDERS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    render_all_gimbal(duration)
