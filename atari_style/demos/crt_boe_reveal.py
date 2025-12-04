#!/usr/bin/env python3
"""CRT Face of Boe Reveal - Unified electron beam deflection model.

The electron beam is ALWAYS the same beam. What changes is what's controlling
the X and Y deflection coils:

1. NO SIGNAL (Lissajous): X/Y deflectors pick up sinusoidal interference
   - Could be 60Hz hum, harmonics, or resonant frequencies
   - Creates coherent but unintended patterns (Lissajous figures)

2. PARTIAL SIGNAL: Deflectors getting some sync but still have interference
   - Horizontal sweep trying to establish
   - Vertical sync partially working
   - Interference still modulating the beam position

3. WEAK/NOISY SIGNAL (Static): Random deflection from noise
   - Background radiation, thermal noise, RF interference
   - No coherent pattern - just chaos
   - This IS "static" - not digital noise, but deflection chaos

4. LOCKED SIGNAL: Deflectors under control, image via intensity modulation
   - But interference NEVER fully goes away
   - Always some wobble, jitter, sync errors

The key insight: Static, Lissajous, and the image are ALL the same beam
being deflected differently. The transition should be continuous.

Usage:
    python -m atari_style.demos.crt_boe_reveal -o boe-reveal.gif --duration 15
"""

import os
import math
import random
import subprocess
import tempfile
import shutil
import platform
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageEnhance

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_IMAGE_PATH = os.path.expanduser("~/Downloads/The_face_of_Boe_(3156086375).jpg")

# CRT phosphor colors - selectable schemes
COLOR_SCHEMES = {
    'green': {
        'bright': (200, 255, 220),
        'normal': (0, 255, 100),
        'dim': (0, 120, 50),
        'black': (4, 6, 4),
    },
    'amber': {
        'bright': (255, 220, 150),
        'normal': (255, 176, 0),
        'dim': (140, 95, 0),
        'black': (8, 5, 2),
    },
    'white': {
        'bright': (255, 255, 255),
        'normal': (200, 200, 210),
        'dim': (100, 100, 110),
        'black': (5, 5, 6),
    },
}

# Default scheme (can be overridden)
CURRENT_SCHEME = 'green'

def get_colors():
    scheme = COLOR_SCHEMES.get(CURRENT_SCHEME, COLOR_SCHEMES['green'])
    return scheme['bright'], scheme['normal'], scheme['dim'], scheme['black']

PHOSPHOR_BRIGHT, PHOSPHOR_GREEN, PHOSPHOR_DIM, CRT_BLACK = get_colors()

# Phase timing - compressed for better pacing
PHASE_LISSAJOUS = 0.08        # Pure Lissajous interference (shorter)
PHASE_BREAKING = 0.18         # Lissajous breaking down, static emerging
PHASE_STATIC_PEAK = 0.28      # Maximum static/chaos
PHASE_LOCKING = 0.45          # Signal trying to lock
PHASE_LOCKED = 0.65           # Image visible but never perfect
# 0.65-1.0: More time with visible image


# =============================================================================
# DEFLECTION MODEL
# =============================================================================

class DeflectionModel:
    """Models the X/Y deflection coils and their various interference sources."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2

        # Deflection ranges
        self.x_range = width // 2 - 20
        self.y_range = height // 2 - 20

    def get_lissajous_deflection(self, t: float, phase_in_trace: float,
                                  a: float, b: float, delta: float,
                                  rotation: float) -> Tuple[float, float]:
        """Get X/Y deflection from sinusoidal interference (Lissajous mode)."""
        # Base Lissajous from interference
        angle = phase_in_trace * 2 * math.pi

        x = math.sin(a * angle + t * 1.5)
        y = math.sin(b * angle + delta + t * 0.8)

        # Apply rotation (interference can rotate the pattern)
        cos_r, sin_r = math.cos(rotation), math.sin(rotation)
        x, y = x * cos_r - y * sin_r, x * sin_r + y * cos_r

        return x, y

    def get_raster_deflection(self, scanline: int, x_pos: float,
                               total_scanlines: int) -> Tuple[float, float]:
        """Get X/Y deflection for proper raster scan."""
        # X: horizontal sweep -1 to 1
        x = x_pos * 2 - 1

        # Y: vertical position based on scanline
        y = (scanline / total_scanlines) * 2 - 1

        return x, y

    def get_noise_deflection(self, t: float, seed: float) -> Tuple[float, float]:
        """Get random deflection from noise/interference (static mode)."""
        # Use coherent noise that varies smoothly
        noise_x = (math.sin(seed * 127.1 + t * 50) +
                   math.sin(seed * 311.7 + t * 73) * 0.5 +
                   math.sin(seed * 74.7 + t * 91) * 0.25)

        noise_y = (math.cos(seed * 269.5 + t * 47) +
                   math.cos(seed * 183.3 + t * 67) * 0.5 +
                   math.cos(seed * 421.3 + t * 83) * 0.25)

        # Normalize to -1, 1 range
        noise_x = noise_x / 1.75
        noise_y = noise_y / 1.75

        return noise_x, noise_y

    def get_h_sync_interference(self, t: float, scanline: int,
                                 interference_level: float) -> float:
        """Horizontal sync interference - makes lines wavy."""
        if interference_level < 0.01:
            return 0.0

        # Multiple interference frequencies
        h_error = (math.sin(t * 2.3 + scanline * 0.1) * 0.15 +
                   math.sin(t * 7.1 + scanline * 0.3) * 0.08 +
                   math.sin(t * 13.7 + scanline * 0.05) * 0.04)

        # Add some randomness (thermal noise)
        h_error += random.gauss(0, 0.02)

        return h_error * interference_level

    def get_v_sync_interference(self, t: float, interference_level: float) -> float:
        """Vertical sync interference - makes frame roll."""
        if interference_level < 0.01:
            return 0.0

        v_error = (math.sin(t * 1.7) * 0.1 +
                   math.sin(t * 0.3) * 0.05)

        return v_error * interference_level


# =============================================================================
# BEAM TRACER
# =============================================================================

class BeamTracer:
    """Traces the electron beam path under various conditions."""

    def __init__(self, width: int, height: int, num_scanlines: int = 240):
        self.width = width
        self.height = height
        self.num_scanlines = num_scanlines
        self.deflection = DeflectionModel(width, height)

    def trace_beam(self, t: float, signal_strength: float,
                   image_intensity: List[List[float]],
                   num_points: int = 4000) -> List[Tuple[int, int, float]]:
        """
        Trace the electron beam path.

        signal_strength: 0 = no signal (Lissajous/static), 1 = full lock
        Returns list of (x, y, intensity) points
        """
        points = []

        # Interference parameters (decrease with signal strength but never zero)
        lissajous_strength = max(0.05, 1.0 - signal_strength * 1.2)
        static_strength = self._get_static_strength(signal_strength)
        raster_strength = min(1.0, signal_strength * 1.5)

        # Lissajous parameters (from interference)
        base_a, base_b = 2.0, 5.0
        chaos = lissajous_strength
        a = base_a + math.sin(t * 6) * 0.3 * chaos
        b = base_b + math.cos(t * 5.5) * 0.4 * chaos
        delta = math.sin(t * 4) * 0.5 * chaos
        rotation = math.pi/2 + t * 5.0 * chaos

        # Interference levels
        h_interference = max(0.05, 1.0 - signal_strength * 0.9)
        v_interference = max(0.03, 1.0 - signal_strength * 0.95)

        img_height = len(image_intensity)
        img_width = len(image_intensity[0]) if img_height > 0 else 0

        # Trace the beam
        for i in range(num_points):
            phase = i / num_points

            # Which scanline would we be on in raster mode?
            scanline = int(phase * self.num_scanlines) % self.num_scanlines
            x_pos_in_line = (phase * self.num_scanlines) % 1.0

            # Get deflection components
            liss_x, liss_y = self.deflection.get_lissajous_deflection(
                t, phase, a, b, delta, rotation
            )

            rast_x, rast_y = self.deflection.get_raster_deflection(
                scanline, x_pos_in_line, self.num_scanlines
            )

            noise_x, noise_y = self.deflection.get_noise_deflection(t, phase * 1000)

            # H-sync and V-sync interference
            h_error = self.deflection.get_h_sync_interference(t, scanline, h_interference)
            v_error = self.deflection.get_v_sync_interference(t, v_interference)

            # BLEND all deflection sources
            # This is the key - everything contributes, weights change
            x = (liss_x * lissajous_strength +
                 rast_x * raster_strength +
                 noise_x * static_strength +
                 h_error)

            y = (liss_y * lissajous_strength +
                 rast_y * raster_strength +
                 noise_y * static_strength +
                 v_error)

            # Normalize (deflection sources can add up > 1)
            total_weight = lissajous_strength + raster_strength + static_strength
            if total_weight > 1.0:
                x /= total_weight
                y /= total_weight

            # Convert to screen coordinates
            screen_x = int(self.deflection.cx + x * self.deflection.x_range)
            screen_y = int(self.deflection.cy + y * self.deflection.y_range)

            # Clamp to screen
            screen_x = max(0, min(self.width - 1, screen_x))
            screen_y = max(0, min(self.height - 1, screen_y))

            # Beam intensity
            # In raster mode, intensity comes from image
            # In Lissajous/static mode, intensity is BRIGHT and uniform
            if raster_strength > 0.3:
                # Get image intensity at current position
                img_y = int((screen_y / self.height) * img_height)
                img_x = int((screen_x / self.width) * img_width)
                img_y = max(0, min(img_height - 1, img_y))
                img_x = max(0, min(img_width - 1, img_x))

                image_val = image_intensity[img_y][img_x]

                # Boost image intensity for visibility
                image_val = min(1.0, image_val * 1.3 + 0.1)

                # Blend image intensity with uniform beam
                uniform_intensity = 0.7 + 0.2 * math.sin(phase * 20 + t * 5)
                intensity = (image_val * raster_strength +
                            uniform_intensity * (1 - raster_strength))
            else:
                # Non-image mode - beam intensity is BRIGHT, varies along trace
                intensity = 0.7 + 0.25 * math.sin(phase * 15 + t * 8)
                intensity += random.gauss(0, 0.08 * static_strength)

            # Add noise to intensity based on interference
            intensity += random.gauss(0, 0.03 * (1 - signal_strength))
            intensity = max(0.2, min(1.0, intensity))

            points.append((screen_x, screen_y, intensity))

        return points

    def _get_static_strength(self, signal_strength: float) -> float:
        """Static is strongest when signal is weak but trying to lock."""
        # Static peaks around signal_strength = 0.3-0.5
        # (trying to lock but failing)
        if signal_strength < 0.3:
            return signal_strength * 2  # Building up
        elif signal_strength < 0.6:
            return 0.6 - (signal_strength - 0.3)  # Peaked, declining
        else:
            return max(0.02, 0.3 - (signal_strength - 0.6) * 0.7)  # Fading but never zero


# =============================================================================
# RENDERING
# =============================================================================

def render_beam_to_frame(beam_points: List[Tuple[int, int, float]],
                         width: int, height: int,
                         signal_strength: float = 0.0) -> Image.Image:
    """Render electron beam points to a frame with phosphor accumulation."""
    # Float buffer for intensity accumulation
    buffer = [[0.0 for _ in range(width)] for _ in range(height)]

    # Higher accumulation when signal is stronger (more scanlines hitting same spots)
    accum_factor = 0.4 + signal_strength * 0.4  # 0.4 to 0.8

    # Accumulate beam hits with phosphor bloom
    for x, y, intensity in beam_points:
        if 0 <= x < width and 0 <= y < height:
            buffer[y][x] = min(1.0, buffer[y][x] + intensity * accum_factor)

            # Phosphor bloom to neighbors - stronger when locked
            bloom_intensity = intensity * (0.1 + signal_strength * 0.15)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    buffer[ny][nx] = min(1.0, buffer[ny][nx] + bloom_intensity)

            # Wider bloom for bright spots
            if intensity > 0.6:
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            dist = math.sqrt(dx*dx + dy*dy)
                            buffer[ny][nx] = min(1.0, buffer[ny][nx] +
                                                intensity * 0.08 / dist)

    # Brightness boost for locked signal
    brightness_boost = 1.0 + signal_strength * 0.6  # Up to 1.6x brighter when locked

    # Convert buffer to image
    frame = Image.new('RGB', (width, height), CRT_BLACK)
    pixels = frame.load()

    for y in range(height):
        for x in range(width):
            intensity = min(1.0, buffer[y][x] * brightness_boost)

            if intensity > 0.015:
                # Phosphor color gradient based on intensity
                if intensity > 0.75:
                    color = PHOSPHOR_BRIGHT
                elif intensity > 0.3:
                    color = PHOSPHOR_GREEN
                else:
                    color = PHOSPHOR_DIM

                r = int(color[0] * intensity)
                g = int(color[1] * intensity)
                b = int(color[2] * intensity)

                pixels[x, y] = (r, g, b)

    return frame


def apply_crt_effects(frame: Image.Image) -> Image.Image:
    """Apply CRT screen effects - curvature vignette."""
    result = frame.copy()
    pixels = result.load()
    cx, cy = frame.width // 2, frame.height // 2

    for y in range(frame.height):
        for x in range(frame.width):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            dist = math.sqrt(dx**2 + dy**2)

            # Vignette
            vignette = max(0.25, 1.0 - (dist * 0.45) ** 2)

            pixel = pixels[x, y]
            pixels[x, y] = tuple(int(c * vignette) for c in pixel)

    return result


# =============================================================================
# IMAGE LOADING
# =============================================================================

def load_image_as_intensity(image_path: str, width: int, height: int) -> List[List[float]]:
    """Load image and convert to 2D intensity array."""
    img = Image.open(image_path).convert('L')

    # Crop to focus on face
    w, h = img.size
    margin = min(w, h) // 12
    img = img.crop((margin, 0, w - margin, h - margin))

    # Resize
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    # Boost contrast
    img = ImageEnhance.Contrast(img).enhance(1.4)

    # Convert to 2D array
    pixels = img.load()
    intensity_map = []
    for y in range(height):
        row = []
        for x in range(width):
            val = pixels[x, y]
            if isinstance(val, tuple):
                val = val[0]
            row.append(val / 255.0)
        intensity_map.append(row)

    return intensity_map


# =============================================================================
# FRAME GENERATION
# =============================================================================

def get_signal_strength(progress: float, mode: str = 'standard') -> float:
    """Get signal strength based on animation progress.

    Modes:
        'standard': Gradual lock, stays locked
        'tease': Lock early (25-30%), blur out, partial resolve at end
    """
    if mode == 'tease':
        # Version 2: Resolve early, blur, partial resolve
        if progress < 0.05:
            # Quick static intro
            return progress * 4  # 0 to 0.2
        elif progress < 0.15:
            # Rapidly locking
            p = (progress - 0.05) / 0.10
            return 0.2 + p * 0.75  # 0.2 to 0.95
        elif progress < 0.35:
            # CLEAR IMAGE - fully locked
            return 0.95
        elif progress < 0.50:
            # Signal degrading - blur out
            p = (progress - 0.35) / 0.15
            return 0.95 - p * 0.55  # 0.95 to 0.4
        elif progress < 0.70:
            # Heavy static/chaos
            p = (progress - 0.50) / 0.20
            return 0.4 - p * 0.15  # 0.4 to 0.25
        elif progress < 0.85:
            # Trying to relock
            p = (progress - 0.70) / 0.15
            return 0.25 + p * 0.45  # 0.25 to 0.70
        else:
            # Partial lock at end - not quite clear
            p = (progress - 0.85) / 0.15
            return 0.70 + p * 0.15  # 0.70 to 0.85
    else:
        # Standard mode - gradual lock
        if progress < PHASE_LISSAJOUS:
            return 0.0
        elif progress < PHASE_BREAKING:
            p = (progress - PHASE_LISSAJOUS) / (PHASE_BREAKING - PHASE_LISSAJOUS)
            return p * 0.2
        elif progress < PHASE_STATIC_PEAK:
            p = (progress - PHASE_BREAKING) / (PHASE_STATIC_PEAK - PHASE_BREAKING)
            return 0.2 + p * 0.15
        elif progress < PHASE_LOCKING:
            p = (progress - PHASE_STATIC_PEAK) / (PHASE_LOCKING - PHASE_STATIC_PEAK)
            return 0.35 + p * 0.35
        elif progress < PHASE_LOCKED:
            p = (progress - PHASE_LOCKING) / (PHASE_LOCKED - PHASE_LOCKING)
            return 0.7 + p * 0.25
        else:
            return 0.95


def generate_frame(t: float, duration: float,
                   tracer: BeamTracer,
                   image_intensity: List[List[float]],
                   mode: str = 'standard') -> Image.Image:
    """Generate a single frame."""
    progress = t / duration
    signal_strength = get_signal_strength(progress, mode)

    # Scale points with resolution and signal strength
    # Need MANY more points when locked to fill in the image clearly
    base_points = tracer.width * tracer.height // 50  # Base on resolution
    num_points = int(base_points * (0.3 + signal_strength * 1.5))

    # Minimum for visibility, maximum for performance
    num_points = max(3000, min(25000, num_points))

    # Trace beam
    beam_points = tracer.trace_beam(t, signal_strength, image_intensity, num_points)

    # Render to frame - pass signal_strength for brightness adjustment
    frame = render_beam_to_frame(beam_points, tracer.width, tracer.height, signal_strength)

    # Apply CRT effects
    frame = apply_crt_effects(frame)

    return frame


# =============================================================================
# VIDEO/GIF RENDERING
# =============================================================================

def render_crt_reveal(output_path: str, duration: float, fps: int,
                      width: int = 640, height: int = 480,
                      image_path: str = None,
                      color_scheme: str = 'green',
                      mode: str = 'standard') -> bool:
    """Render the CRT reveal animation."""
    global CURRENT_SCHEME, PHOSPHOR_BRIGHT, PHOSPHOR_GREEN, PHOSPHOR_DIM, CRT_BLACK

    # Set color scheme
    CURRENT_SCHEME = color_scheme
    PHOSPHOR_BRIGHT, PHOSPHOR_GREEN, PHOSPHOR_DIM, CRT_BLACK = get_colors()
    print(f"Color scheme: {color_scheme}")
    print(f"Signal mode: {mode}")

    if image_path is None:
        image_path = DEFAULT_IMAGE_PATH
    image_path = os.path.expanduser(image_path)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return False

    print(f"Loading: {image_path}")
    image_intensity = load_image_as_intensity(image_path, width, height)
    print(f"Loaded {width}x{height} intensity map")

    tracer = BeamTracer(width, height)

    # Find ffmpeg
    ffmpeg_cmd = 'ffmpeg'
    if platform.system() == 'Windows':
        scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
        if os.path.exists(scoop_ffmpeg):
            ffmpeg_cmd = scoop_ffmpeg

    temp_dir = tempfile.mkdtemp(prefix='crt_boe_')
    print(f"Rendering to: {temp_dir}")

    is_gif = output_path.lower().endswith('.gif')

    try:
        total_frames = int(duration * fps)

        for i in range(total_frames):
            t = i / fps
            frame = generate_frame(t, duration, tracer, image_intensity, mode)
            frame.save(os.path.join(temp_dir, f"frame_{i:05d}.png"))

            if (i + 1) % 30 == 0:
                pct = (i + 1) / total_frames * 100
                progress = t / duration
                sig = get_signal_strength(progress, mode)
                print(f"  Frame {i+1}/{total_frames} ({pct:.0f}%) signal={sig:.2f}")

        print(f"Encoding {'GIF' if is_gif else 'MP4'}...")
        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')

        if is_gif:
            palette_path = os.path.join(temp_dir, 'palette.png')
            subprocess.run([ffmpeg_cmd, '-y', '-framerate', str(fps),
                          '-i', frame_pattern, '-vf', 'palettegen=stats_mode=diff',
                          palette_path], capture_output=True)

            result = subprocess.run([ffmpeg_cmd, '-y', '-framerate', str(fps),
                                    '-i', frame_pattern, '-i', palette_path,
                                    '-lavfi', 'paletteuse=dither=bayer:bayer_scale=5',
                                    output_path], capture_output=True, text=True)
        else:
            result = subprocess.run([ffmpeg_cmd, '-y', '-framerate', str(fps),
                                    '-i', frame_pattern, '-c:v', 'libx264',
                                    '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
                                    output_path], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Encoding failed: {result.stderr}")
            return False

        size_kb = os.path.getsize(output_path) / 1024
        print(f"Success! {output_path} ({size_kb:.1f} KB)")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CRT Reveal - Unified electron beam deflection model"
    )

    parser.add_argument('-o', '--output', default='boe-crt-reveal.gif')
    parser.add_argument('--duration', type=float, default=15)
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--image', type=str, default=None)
    parser.add_argument('--color', type=str, default='green',
                       choices=['green', 'amber', 'white'],
                       help='CRT phosphor color scheme')
    parser.add_argument('--mode', type=str, default='standard',
                       choices=['standard', 'tease'],
                       help='Signal mode: standard (gradual lock) or tease (lock-blur-partial)')

    args = parser.parse_args()

    print("CRT Face of Boe Reveal - Unified Deflection Model")
    print("=" * 55)
    print("All effects are the SAME electron beam:")
    print("  - Lissajous = sinusoidal interference on deflectors")
    print("  - Static = noise/RF interference on deflectors")
    print("  - Image = controlled deflection + intensity modulation")
    print("  - Everything blends continuously, nothing is overlaid")
    print()
    print(f"Phases ({args.duration}s @ {args.fps}fps):")
    print(f"  0-{int(PHASE_LISSAJOUS*100)}%: Pure Lissajous (interference pattern)")
    print(f"  {int(PHASE_LISSAJOUS*100)}-{int(PHASE_BREAKING*100)}%: Pattern breaking down")
    print(f"  {int(PHASE_BREAKING*100)}-{int(PHASE_STATIC_PEAK*100)}%: Peak static (signal failing)")
    print(f"  {int(PHASE_STATIC_PEAK*100)}-{int(PHASE_LOCKING*100)}%: Signal locking")
    print(f"  {int(PHASE_LOCKING*100)}-{int(PHASE_LOCKED*100)}%: Image emerging")
    print(f"  {int(PHASE_LOCKED*100)}-100%: Locked (but never perfect)")
    print()

    success = render_crt_reveal(args.output, args.duration, args.fps,
                                args.width, args.height, args.image,
                                args.color, args.mode)
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
