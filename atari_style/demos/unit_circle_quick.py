"""Unit Circle Quick Test - Minimal video generation to verify pipeline.

Creates a 5-second test video using file-based frames (more Windows-compatible).
"""

import os
import sys
import math
import subprocess
import tempfile
import shutil
import platform
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple

# Dracula palette
COLOR_RGB = {
    'cyan': (139, 233, 253),
    'magenta': (255, 121, 198),
    'green': (80, 250, 123),
    'yellow': (241, 250, 140),
    'white': (248, 248, 242),
}


def find_font(size: int):
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


def render_frame(frame_num: int, total_frames: int, width: int, height: int) -> Image.Image:
    """Render a single frame of unit circle animation."""
    img = Image.new('RGB', (width, height), (30, 32, 44))
    draw = ImageDraw.Draw(img)

    t = frame_num / 15  # time in seconds at 15fps
    theta = t * 2  # angular velocity

    # Circle center and radius
    cx, cy = width // 3, height // 2
    radius = min(width, height) // 3

    # Draw axes
    draw.line([(cx - radius - 20, cy), (cx + radius + 20, cy)], fill=(60, 60, 80), width=1)
    draw.line([(cx, cy - radius - 20), (cx, cy + radius + 20)], fill=(60, 60, 80), width=1)

    # Draw circle
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                outline=COLOR_RGB['cyan'], width=2)

    # Point on circle
    px = cx + int(radius * math.cos(theta))
    py = cy - int(radius * math.sin(theta))

    # Radial line
    draw.line([(cx, cy), (px, py)], fill=COLOR_RGB['green'], width=3)

    # Projections
    draw.line([(px, cy), (px, py)], fill=COLOR_RGB['magenta'], width=2)
    draw.line([(cx, py), (px, py)], fill=COLOR_RGB['cyan'], width=2)

    # Point
    draw.ellipse([(px - 8, py - 8), (px + 8, py + 8)], fill=COLOR_RGB['yellow'])
    draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=COLOR_RGB['white'])

    # Title
    font = find_font(24)
    draw.text((20, 20), "Unit Circle Test", font=font, fill=COLOR_RGB['white'])
    draw.text((20, 50), f"t = {t:.2f}s  theta = {math.degrees(theta):.0f} deg",
             font=find_font(18), fill=COLOR_RGB['cyan'])

    # Sine wave on right side
    wave_x = cx + radius + 50
    wave_width = width - wave_x - 20
    wave_cy = cy

    # Axis
    draw.line([(wave_x, wave_cy), (wave_x + wave_width, wave_cy)], fill=(60, 60, 80), width=1)

    # Wave
    prev = None
    for x in range(wave_width):
        wave_t = (x / wave_width) * 2 * math.pi
        y = wave_cy - int(radius * 0.8 * math.sin(wave_t + theta))
        if prev:
            draw.line([prev, (wave_x + x, y)], fill=COLOR_RGB['cyan'], width=2)
        prev = (wave_x + x, y)

    return img


def run_quick_test(output_path: str = None, duration: int = 5, fps: int = 15):
    """Generate a quick test video."""
    width, height = 960, 540  # 540p for speed
    total_frames = duration * fps

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'unit-circle-test.mp4')
        output_path = os.path.abspath(output_path)

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix='unit_circle_')

    print(f"Unit Circle Quick Test")
    print(f"=" * 40)
    print(f"Resolution: {width}x{height}")
    print(f"Duration: {duration}s @ {fps}fps = {total_frames} frames")
    print(f"Temp dir: {temp_dir}")
    print(f"Output: {output_path}")
    print()

    try:
        # Render frames
        print("Rendering frames...")
        for i in range(total_frames):
            img = render_frame(i, total_frames, width, height)
            frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
            img.save(frame_path, optimize=False)

            if (i + 1) % 15 == 0:
                print(f"  Frame {i + 1}/{total_frames}")

        print(f"\nFrames complete. Running ffmpeg...")

        # Find ffmpeg
        ffmpeg = 'ffmpeg'
        if platform.system() == 'Windows':
            scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
            if os.path.exists(scoop_ffmpeg):
                ffmpeg = scoop_ffmpeg

        # Encode
        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')
        cmd = [
            ffmpeg, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'fast',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size = os.path.getsize(output_path)
            print(f"\nSuccess!")
            print(f"Output: {output_path}")
            print(f"Size: {size / 1024:.1f} KB")
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    finally:
        # Cleanup
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Quick unit circle test video')
    parser.add_argument('--output', '-o', help='Output path')
    parser.add_argument('--duration', '-d', type=int, default=5, help='Duration in seconds')
    args = parser.parse_args()

    success = run_quick_test(args.output, args.duration)
    sys.exit(0 if success else 1)
