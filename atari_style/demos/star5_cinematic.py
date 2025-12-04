#!/usr/bin/env python3
"""Star-5 Cinematic Video - Dramatic Lissajous with rotation, color morphing, and instability.

Creates a YouTube-ready video featuring the Star-5 (2:5) Lissajous pattern with:
- 90-degree rotation from standard orientation
- Smooth color theme transitions (ocean → desert → forest → mountain → ocean)
- Deliberate instability wobbles for dramatic effect
- Projection mapping illusions (perspective shifts, depth pulses)

Usage:
    python -m atari_style.demos.star5_cinematic -o star5-cinematic.gif --duration 30
    python -m atari_style.demos.star5_cinematic -o star5-cinematic.mp4 --duration 60 --fps 30
"""

import os
import math
import subprocess
import tempfile
import shutil
import platform
from typing import Generator, List, Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont


# =============================================================================
# COLOR THEMES - Will morph between these
# =============================================================================

THEMES = {
    'ocean': ['#6272a4', '#8be9fd', '#50fa7b', '#8be9fd', '#bd93f9', '#f8f8f2'],
    'desert': ['#ffb86c', '#f1fa8c', '#ff5555', '#ff79c6', '#ffb86c', '#f8f8f2'],
    'forest': ['#50fa7b', '#8be9fd', '#f1fa8c', '#50fa7b', '#6272a4', '#f8f8f2'],
    'mountain': ['#f8f8f2', '#8be9fd', '#bd93f9', '#6272a4', '#ff79c6', '#bd93f9'],
}

THEME_ORDER = ['ocean', 'desert', 'forest', 'mountain', 'ocean']  # Loop back


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """Linear interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def get_morphed_palette(progress: float) -> List[Tuple[int, int, int]]:
    """Get palette smoothly morphed between themes based on progress (0-1)."""
    # Map progress to theme transitions
    num_transitions = len(THEME_ORDER) - 1
    segment = progress * num_transitions
    idx = min(int(segment), num_transitions - 1)
    local_t = segment - idx

    theme1 = THEME_ORDER[idx]
    theme2 = THEME_ORDER[idx + 1]

    palette1 = [hex_to_rgb(c) for c in THEMES[theme1]]
    palette2 = [hex_to_rgb(c) for c in THEMES[theme2]]

    # Smooth easing
    eased_t = (1 - math.cos(local_t * math.pi)) / 2

    return [lerp_color(palette1[i], palette2[i], eased_t) for i in range(len(palette1))]


# =============================================================================
# INSTABILITY PATTERNS - For dramatic wobbles
# =============================================================================

@dataclass
class InstabilityWave:
    """A wave of instability that passes through the pattern."""
    frequency: float      # How fast the wave oscillates
    amplitude: float      # Strength of the disturbance
    duration: float       # How long it lasts
    start_time: float     # When it begins


def get_instability(t: float, duration: float) -> Tuple[float, float, float]:
    """Calculate instability offsets for a, b, delta at time t.

    Creates deliberate "chaos excursions" synced with camera movements.
    Pattern destabilizes during spins and settles during holds.
    """
    progress = t / duration

    # Base stable values for Star-5
    base_a, base_b, base_delta = 2.0, 5.0, 0.0

    offset_a = 0.0
    offset_b = 0.0
    offset_delta = 0.0

    # ==========================================================================
    # BREATHING - Always present, subtle life
    # ==========================================================================
    offset_a += math.sin(t * 0.25) * 0.06
    offset_b += math.cos(t * 0.2) * 0.08
    offset_delta += math.sin(t * 0.15) * 0.1

    # ==========================================================================
    # CHAOS DURING SPINS - Pattern goes wild when camera spins
    # ==========================================================================
    # Spin periods: 0.08-0.15, 0.25-0.32, 0.45-0.52, 0.85-0.92
    spin_chaos_periods = [
        (0.08, 0.15, 1.0),   # First spin - moderate chaos
        (0.25, 0.32, 1.2),   # Reverse spin - more intense
        (0.45, 0.52, 1.5),   # Big spin - even more
        (0.85, 0.92, 2.0),   # Final spin - maximum chaos!
    ]

    for start, end, intensity_mult in spin_chaos_periods:
        if start <= progress <= end:
            local_p = (progress - start) / (end - start)
            # Ramp up then down within spin
            envelope = math.sin(local_p * math.pi)
            intensity = envelope * intensity_mult

            # Chaotic frequency modulation
            offset_a += math.sin(t * 6) * 0.25 * intensity
            offset_a += math.sin(t * 11) * 0.1 * intensity
            offset_b += math.cos(t * 5.5) * 0.35 * intensity
            offset_b += math.cos(t * 9) * 0.15 * intensity
            offset_delta += math.sin(t * 4) * 0.4 * intensity

    # ==========================================================================
    # STABILITY DURING HOLDS - Pattern crystallizes beautifully
    # ==========================================================================
    # Hold periods: 0.15-0.25, 0.52-0.65
    hold_periods = [
        (0.15, 0.25),  # First dramatic hold
        (0.52, 0.65),  # Long contemplative hold
    ]

    for start, end in hold_periods:
        if start <= progress <= end:
            local_p = (progress - start) / (end - start)
            # Dampen all oscillations during holds
            damping = 0.3 + 0.7 * (1.0 - math.sin(local_p * math.pi))
            offset_a *= damping
            offset_b *= damping
            offset_delta *= damping

    # ==========================================================================
    # IMPACT HITS - Sharp jolts at spin stops
    # ==========================================================================
    impact_moments = [0.15, 0.32, 0.52, 0.92]
    for moment in impact_moments:
        dist = abs(progress - moment)
        if dist < 0.02:
            intensity = 1.0 - (dist / 0.02)
            # Sharp spike then quick decay
            spike = intensity ** 0.5
            offset_a += math.sin(t * 20) * 0.15 * spike
            offset_b += math.cos(t * 18) * 0.2 * spike

    # ==========================================================================
    # TENSION BUILD - Increasing instability toward climax
    # ==========================================================================
    if 0.75 <= progress <= 0.85:
        tension = (progress - 0.75) / 0.10
        offset_a += math.sin(t * 3) * 0.1 * tension
        offset_b += math.cos(t * 2.5) * 0.15 * tension
        offset_delta += math.sin(t * 2) * 0.2 * tension

    # ==========================================================================
    # SHIMMER - High frequency detail (always subtle)
    # ==========================================================================
    offset_a += math.sin(t * 12) * 0.008
    offset_b += math.cos(t * 11) * 0.01

    return (base_a + offset_a, base_b + offset_b, base_delta + offset_delta)


# =============================================================================
# ROTATION & PROJECTION EFFECTS
# =============================================================================

def apply_rotation(x: float, y: float, angle: float) -> Tuple[float, float]:
    """Rotate point (x, y) by angle radians around origin."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


def apply_perspective(x: float, y: float, z: float, fov: float = 1.5) -> Tuple[float, float]:
    """Apply simple perspective projection for depth effect."""
    scale = fov / (fov + z)
    return (x * scale, y * scale)


def get_projection_params(t: float, duration: float) -> dict:
    """Get time-varying projection parameters for dramatic 'The Office' style camera work.

    Features spin-and-stop effects, dramatic zooms, pans, and tilts
    like a documentary camera operator following the action.
    """
    progress = t / duration

    # ==========================================================================
    # ROTATION - Fast spins with dramatic stops (The Office whip-pan style)
    # ==========================================================================

    # Define spin segments: (start_progress, end_progress, spin_speed, final_hold)
    # Speed in radians/sec, negative = reverse
    spin_segments = [
        # Opening: slow reveal
        (0.00, 0.08, 0.3, True),
        # First fast spin
        (0.08, 0.15, 3.5, True),
        # Hold and breathe
        (0.15, 0.25, 0.1, False),
        # Reverse spin!
        (0.25, 0.32, -4.0, True),
        # Gentle drift
        (0.32, 0.45, 0.5, False),
        # Another fast spin
        (0.45, 0.52, 5.0, True),
        # Long dramatic hold
        (0.52, 0.65, 0.05, False),
        # Slow reverse
        (0.65, 0.75, -1.5, True),
        # Building tension - accelerating
        (0.75, 0.85, 2.0, False),
        # Final dramatic spin
        (0.85, 0.92, 6.0, True),
        # Ending - slow down to rest
        (0.92, 1.00, 0.2, False),
    ]

    # Calculate rotation based on segments
    base_rotation = math.pi / 2  # Start at 90 degrees
    rotation = base_rotation

    for start, end, speed, do_ease in spin_segments:
        if progress < start:
            break
        elif progress < end:
            segment_progress = (progress - start) / (end - start)
            if do_ease:
                # Ease out for dramatic stop
                eased = 1.0 - (1.0 - segment_progress) ** 3
            else:
                eased = segment_progress
            segment_duration = (end - start) * duration
            rotation += speed * segment_duration * eased
            break
        else:
            # Completed segment
            segment_duration = (end - start) * duration
            rotation += speed * segment_duration

    # ==========================================================================
    # ZOOM (Z-offset) - Documentary style push-ins and pull-outs
    # ==========================================================================

    # Base gentle breathing
    z_offset = math.sin(t * 0.3) * 0.15

    # Dramatic zoom moments (like zooming in on someone's reaction)
    zoom_moments = [
        (0.12, 0.18, 0.6),   # Push in during first spin stop
        (0.30, 0.35, -0.4),  # Pull back reveal
        (0.50, 0.55, 0.8),   # Big push in
        (0.63, 0.68, -0.3),  # Slow pull out
        (0.88, 0.95, 0.7),   # Final dramatic push
    ]

    for start, end, intensity in zoom_moments:
        if start <= progress <= end:
            local_p = (progress - start) / (end - start)
            # Smooth in and out
            smooth = math.sin(local_p * math.pi)
            z_offset += intensity * smooth

    # ==========================================================================
    # PAN (Tilt X) - Side to side camera movement
    # ==========================================================================

    # Base gentle sway
    tilt_x = math.sin(t * 0.2) * 0.08

    # Whip pans at spin stops
    whip_pan_moments = [0.15, 0.32, 0.52, 0.75, 0.92]
    for moment in whip_pan_moments:
        dist = abs(progress - moment)
        if dist < 0.04:
            intensity = 1.0 - (dist / 0.04)
            # Quick whip then settle
            whip = math.sin((progress - moment + 0.04) / 0.08 * math.pi * 2) * intensity
            tilt_x += whip * 0.25

    # ==========================================================================
    # TILT (Tilt Y) - Up and down nods
    # ==========================================================================

    # Base subtle nod
    tilt_y = math.cos(t * 0.25) * 0.06

    # Dramatic nods at key moments
    nod_moments = [0.20, 0.40, 0.60, 0.80]
    for moment in nod_moments:
        dist = abs(progress - moment)
        if dist < 0.03:
            intensity = 1.0 - (dist / 0.03)
            tilt_y += math.sin(intensity * math.pi) * 0.2

    # ==========================================================================
    # SCALE - Breathing and impact hits
    # ==========================================================================

    # Base breathing
    scale_pulse = 1.0 + math.sin(t * 0.4) * 0.05

    # Impact hits at spin stops (like a camera jolt)
    for moment in whip_pan_moments:
        dist = abs(progress - moment)
        if dist < 0.03:
            intensity = 1.0 - (dist / 0.03)
            # Quick expand then contract
            scale_pulse += intensity * 0.12 * math.cos(intensity * math.pi * 2)

    # Tension building scale increase near end
    if progress > 0.85:
        tension = (progress - 0.85) / 0.15
        scale_pulse += tension * 0.1

    return {
        'rotation': rotation,
        'z_offset': z_offset,
        'tilt_x': tilt_x,
        'tilt_y': tilt_y,
        'scale': scale_pulse,
    }


# =============================================================================
# CANVAS RENDERING
# =============================================================================

def find_monospace_font(size: int):
    """Find a suitable monospace font."""
    paths = []
    if platform.system() == 'Windows':
        paths = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]

    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()


class CinematicCanvas:
    """High-quality canvas for cinematic rendering."""

    def __init__(self, cols: int = 160, rows: int = 45, cell_width: int = 10, cell_height: int = 18):
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height

        self.img_width = cols * cell_width
        self.img_height = rows * cell_height

        self.buffer = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.color_buffer = [[(255, 255, 255) for _ in range(cols)] for _ in range(rows)]

        self.bg_color = (30, 32, 44)  # Dark terminal background
        self.font = find_monospace_font(cell_height - 2)

    def clear(self):
        for y in range(self.rows):
            for x in range(self.cols):
                self.buffer[y][x] = ' '
                self.color_buffer[y][x] = (255, 255, 255)

    def set_pixel(self, x: int, y: int, char: str, color: Tuple[int, int, int]):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.buffer[y][x] = char[0] if char else ' '
            self.color_buffer[y][x] = color

    def render(self) -> Image.Image:
        img = Image.new('RGB', (self.img_width, self.img_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for y in range(self.rows):
            for x in range(self.cols):
                char = self.buffer[y][x]
                if char == ' ':
                    continue

                rgb = self.color_buffer[y][x]
                px = x * self.cell_width
                py = y * self.cell_height
                draw.text((px, py), char, font=self.font, fill=rgb)

        return img


# =============================================================================
# MAIN DRAWING FUNCTION
# =============================================================================

def draw_star5_cinematic(canvas: CinematicCanvas, t: float, duration: float):
    """Draw the Star-5 pattern with all cinematic effects."""

    # Get time-varying parameters
    a, b, delta = get_instability(t, duration)
    proj = get_projection_params(t, duration)
    progress = t / duration
    palette = get_morphed_palette(progress)

    # Canvas center
    cx = canvas.cols // 2
    cy = canvas.rows // 2

    # Scale factors (adjusted for terminal aspect ratio)
    base_scale_x = canvas.cols // 3
    base_scale_y = canvas.rows // 3

    # Apply projection scale
    scale_x = base_scale_x * proj['scale']
    scale_y = base_scale_y * proj['scale']

    # Number of points (high for smooth curves)
    points = 800
    trail_chars = ['●', '○', '◦', '·', '.', '.']
    trail_count = 8

    # Draw trails (older = dimmer)
    for trail in range(trail_count - 1, 0, -1):
        trail_t = t - trail * 0.02
        trail_a, trail_b, trail_delta = get_instability(trail_t, duration)

        # Fade factor for trails
        fade = 1.0 - (trail / trail_count)

        for i in range(points):
            angle = (i / points) * 2 * math.pi

            # Lissajous equations
            px = math.sin(trail_a * angle + trail_t * 1.5)
            py = math.sin(trail_b * angle + trail_delta + trail_t * 0.8)

            # Apply tilt for 3D illusion
            px += proj['tilt_x'] * py * 0.5
            py += proj['tilt_y'] * px * 0.5

            # Apply rotation (90 degrees + continuous)
            px, py = apply_rotation(px, py, proj['rotation'])

            # Apply perspective
            z = proj['z_offset'] + math.sin(angle * 2) * 0.1
            px, py = apply_perspective(px, py, z)

            # Map to screen
            screen_x = int(cx + px * scale_x * 1.4)
            screen_y = int(cy + py * scale_y * 0.85)

            if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
                # Color from palette with fade
                color_idx = int((i / points) * len(palette))
                base_color = palette[color_idx % len(palette)]
                faded_color = tuple(int(c * fade * 0.6) for c in base_color)

                char_idx = min(trail, len(trail_chars) - 1)
                canvas.set_pixel(screen_x, screen_y, trail_chars[char_idx], faded_color)

    # Draw current curve (brightest)
    for i in range(points):
        angle = (i / points) * 2 * math.pi

        px = math.sin(a * angle + t * 1.5)
        py = math.sin(b * angle + delta + t * 0.8)

        # Apply tilt
        px += proj['tilt_x'] * py * 0.5
        py += proj['tilt_y'] * px * 0.5

        # Apply rotation
        px, py = apply_rotation(px, py, proj['rotation'])

        # Apply perspective
        z = proj['z_offset'] + math.sin(angle * 2) * 0.1
        px, py = apply_perspective(px, py, z)

        # Map to screen
        screen_x = int(cx + px * scale_x * 1.4)
        screen_y = int(cy + py * scale_y * 0.85)

        if 0 <= screen_x < canvas.cols and 0 <= screen_y < canvas.rows:
            color_idx = int((i / points) * len(palette))
            color = palette[color_idx % len(palette)]
            canvas.set_pixel(screen_x, screen_y, '●', color)


def draw_info_overlay(canvas: CinematicCanvas, t: float, duration: float):
    """Draw subtle info overlay."""
    progress = t / duration

    # Current theme indicator (top right, subtle)
    num_transitions = len(THEME_ORDER) - 1
    segment = progress * num_transitions
    idx = min(int(segment), num_transitions - 1)
    theme_name = THEME_ORDER[idx].upper()

    # Theme name in corner
    for i, char in enumerate(theme_name):
        canvas.set_pixel(canvas.cols - len(theme_name) - 2 + i, 1, char, (100, 100, 120))

    # Pattern name (bottom left, subtle)
    pattern = "STAR-5"
    for i, char in enumerate(pattern):
        canvas.set_pixel(2 + i, canvas.rows - 2, char, (80, 80, 100))


# =============================================================================
# VIDEO/GIF GENERATION
# =============================================================================

def generate_cinematic_frames(duration: float, fps: int,
                              cols: int = 160, rows: int = 45
                              ) -> Generator[Image.Image, None, None]:
    """Generate all frames for the cinematic video."""

    canvas = CinematicCanvas(cols=cols, rows=rows)
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps

        canvas.clear()
        draw_star5_cinematic(canvas, t, duration)
        draw_info_overlay(canvas, t, duration)

        yield canvas.render()


def render_video(output_path: str, duration: float, fps: int,
                 cols: int = 160, rows: int = 45) -> bool:
    """Render frames to video or GIF."""

    # Detect output format
    is_gif = output_path.lower().endswith('.gif')

    # Find ffmpeg
    ffmpeg_cmd = 'ffmpeg'
    if platform.system() == 'Windows':
        scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
        if os.path.exists(scoop_ffmpeg):
            ffmpeg_cmd = scoop_ffmpeg

    temp_dir = tempfile.mkdtemp(prefix='star5_cinematic_')
    print(f"Rendering frames to: {temp_dir}")
    print(f"Canvas: {cols}x{rows} chars")

    try:
        # Generate and save frames
        frame_count = 0
        for i, frame in enumerate(generate_cinematic_frames(duration, fps, cols, rows)):
            frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
            frame.save(frame_path)
            frame_count += 1

            if (i + 1) % 30 == 0:
                progress = (i + 1) / (duration * fps) * 100
                print(f"  Frame {i + 1} ({progress:.0f}%)...")

        print(f"Total frames: {frame_count}")

        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')

        if is_gif:
            print("Encoding GIF (two-pass palette)...")
            palette_path = os.path.join(temp_dir, 'palette.png')

            # Pass 1: Generate palette
            palette_cmd = [
                ffmpeg_cmd, '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-vf', 'palettegen=stats_mode=diff',
                palette_path
            ]
            subprocess.run(palette_cmd, capture_output=True)

            # Pass 2: Encode GIF
            gif_cmd = [
                ffmpeg_cmd, '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-i', palette_path,
                '-lavfi', 'paletteuse=dither=bayer:bayer_scale=5',
                output_path
            ]
            result = subprocess.run(gif_cmd, capture_output=True, text=True)

        else:
            print("Encoding MP4...")
            video_cmd = [
                ffmpeg_cmd, '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-c:v', 'libx264',
                '-preset', 'slow',
                '-crf', '18',
                '-pix_fmt', 'yuv420p',
                output_path
            ]
            result = subprocess.run(video_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Encoding failed: {result.stderr}")
            return False

        size = os.path.getsize(output_path) / 1024
        print(f"Success! {output_path} ({size:.1f} KB)")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Star-5 Cinematic - Dramatic Lissajous video with rotation and color morphing"
    )

    parser.add_argument('-o', '--output', default='star5-cinematic.gif',
                       help='Output path (.gif or .mp4)')
    parser.add_argument('--duration', type=float, default=20,
                       help='Duration in seconds (default: 20)')
    parser.add_argument('--fps', type=int, default=24,
                       help='Frames per second (default: 24)')
    parser.add_argument('--cols', type=int, default=160,
                       help='Terminal columns (default: 160)')
    parser.add_argument('--rows', type=int, default=45,
                       help='Terminal rows (default: 45)')

    args = parser.parse_args()

    print(f"Star-5 Cinematic Renderer")
    print(f"Duration: {args.duration}s @ {args.fps}fps")
    print(f"Effects: Rotation, Color Morphing, Instability Waves, Perspective")

    success = render_video(
        args.output, args.duration, args.fps,
        args.cols, args.rows
    )

    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
