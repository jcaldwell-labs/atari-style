"""Generate showcase video for GPU Mandelbrot visualizer.

Creates a demo video that cycles through presets with smooth transitions
and color palette changes.
"""

import os
import sys
import time
import math
import shutil
import tempfile
import subprocess
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow and numpy required: pip install Pillow numpy")
    sys.exit(1)

from .gl_mandelbrot import GLMandelbrot


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    """Smooth ease in/out curve."""
    return t * t * (3 - 2 * t)


def render_demo_video(
    output_path: str = "mandelbrot_demo.mp4",
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    preset_duration: float = 5.0,
    transition_duration: float = 2.0
):
    """Render a showcase demo video.

    Args:
        output_path: Output MP4 path
        width: Video width
        height: Video height
        fps: Frames per second
        preset_duration: Seconds to hold each preset
        transition_duration: Seconds for transitions
    """
    print(f"Rendering Mandelbrot Demo Video")
    print(f"Resolution: {width}x{height} @ {fps}fps")
    print("=" * 50)

    # Create renderer
    mb = GLMandelbrot(width=width, height=height, headless=True)
    info = mb.get_info()
    print(f"GPU: {info['renderer']}")
    print(f"Software rendering: {info['using_software_rendering']}")

    # Demo sequence: each entry is (preset_index, color_mode, zoom_target)
    # We'll smoothly transition between these
    sequence = [
        # Start with full set, classic colors
        {'preset': 0, 'color': 0, 'zoom_mult': 1.0, 'hold': preset_duration},
        # Zoom into Seahorse Valley with fire colors
        {'preset': 1, 'color': 1, 'zoom_mult': 2.0, 'hold': preset_duration},
        # Elephant Valley with rainbow
        {'preset': 2, 'color': 2, 'zoom_mult': 1.5, 'hold': preset_duration},
        # Spiral with classic
        {'preset': 3, 'color': 0, 'zoom_mult': 3.0, 'hold': preset_duration},
        # Mini Mandelbrot with grayscale
        {'preset': 4, 'color': 3, 'zoom_mult': 2.0, 'hold': preset_duration},
        # Back to full set
        {'preset': 0, 'color': 2, 'zoom_mult': 1.0, 'hold': preset_duration},
    ]

    # Calculate total frames
    total_time = sum(s['hold'] for s in sequence) + transition_duration * (len(sequence) - 1)
    total_frames = int(total_time * fps)

    print(f"Total duration: {total_time:.1f}s ({total_frames} frames)")
    print()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='mandelbrot_demo_')

    try:
        frame_num = 0
        current_time = 0.0
        dt = 1.0 / fps

        # Current interpolated state
        current_zoom = mb.PRESETS[0]['zoom']
        current_cx = mb.PRESETS[0]['center'][0]
        current_cy = mb.PRESETS[0]['center'][1]
        current_color = 0.0

        for seq_idx, seq in enumerate(sequence):
            # Get target state
            preset = mb.PRESETS[seq['preset']]
            target_zoom = preset['zoom'] * seq['zoom_mult']
            target_cx, target_cy = preset['center']
            target_color = seq['color']

            # Hold phase
            hold_frames = int(seq['hold'] * fps)
            print(f"[{seq_idx+1}/{len(sequence)}] {preset['name']} ({seq['hold']:.0f}s hold)")

            for i in range(hold_frames):
                # Slight zoom animation during hold
                zoom_wobble = 1.0 + 0.05 * math.sin(current_time * 0.5)

                mb.zoom = target_zoom * zoom_wobble
                mb.center_x = target_cx
                mb.center_y = target_cy
                mb.color_mode = target_color
                mb.update(dt, None)

                # Render frame
                arr = mb.render_to_array()
                img = Image.fromarray(arr, 'RGBA').convert('RGB')

                # Add text overlay
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
                    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
                except:
                    font = ImageFont.load_default()
                    small_font = font

                # Title
                draw.text((20, 20), "GPU Mandelbrot", fill=(255, 255, 255), font=font)
                draw.text((20, 60), f"Preset: {preset['name']}", fill=(200, 200, 200), font=small_font)
                draw.text((20, 90), f"Zoom: {mb.zoom:.2e}", fill=(200, 200, 200), font=small_font)
                color_names = ['Classic', 'Fire', 'Rainbow', 'Grayscale']
                draw.text((20, 120), f"Colors: {color_names[target_color]}", fill=(200, 200, 200), font=small_font)

                # Save frame
                frame_path = os.path.join(temp_dir, f'frame_{frame_num:05d}.png')
                img.save(frame_path)

                frame_num += 1
                current_time += dt

                if frame_num % fps == 0:
                    print(f"  Frame {frame_num}/{total_frames} ({frame_num/total_frames*100:.0f}%)")

            # Update current state for next transition
            current_zoom = target_zoom
            current_cx = target_cx
            current_cy = target_cy
            current_color = float(target_color)

            # Transition to next (if not last)
            if seq_idx < len(sequence) - 1:
                next_seq = sequence[seq_idx + 1]
                next_preset = mb.PRESETS[next_seq['preset']]
                next_zoom = next_preset['zoom'] * next_seq['zoom_mult']
                next_cx, next_cy = next_preset['center']
                next_color = next_seq['color']

                trans_frames = int(transition_duration * fps)
                print(f"  Transitioning to {next_preset['name']}...")

                for i in range(trans_frames):
                    t = ease_in_out(i / trans_frames)

                    # Interpolate in log space for zoom
                    mb.zoom = math.exp(lerp(math.log(current_zoom), math.log(next_zoom), t))
                    mb.center_x = lerp(current_cx, next_cx, t)
                    mb.center_y = lerp(current_cy, next_cy, t)
                    # Snap color mode (no interpolation)
                    mb.color_mode = next_color if t > 0.5 else int(current_color)
                    mb.update(dt, None)

                    # Render
                    arr = mb.render_to_array()
                    img = Image.fromarray(arr, 'RGBA').convert('RGB')

                    # Minimal overlay during transition
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
                    except:
                        font = ImageFont.load_default()
                    draw.text((20, 20), "GPU Mandelbrot", fill=(255, 255, 255), font=font)

                    frame_path = os.path.join(temp_dir, f'frame_{frame_num:05d}.png')
                    img.save(frame_path)

                    frame_num += 1
                    current_time += dt

        print(f"\nRendered {frame_num} frames")

        # Encode with ffmpeg
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg is None:
            print("ERROR: ffmpeg not found")
            return False

        print(f"Encoding video...")
        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')
        cmd = [
            ffmpeg, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',
            '-preset', 'fast',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            print(f"\nSaved: {output_path}")
            print(f"Size: {file_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    finally:
        mb.release()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate Mandelbrot demo video')
    parser.add_argument('--output', '-o', default='mandelbrot_demo.mp4',
                        help='Output path')
    parser.add_argument('--width', '-W', type=int, default=1920)
    parser.add_argument('--height', '-H', type=int, default=1080)
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--preset-duration', type=float, default=5.0,
                        help='Seconds per preset')
    parser.add_argument('--transition', type=float, default=2.0,
                        help='Transition duration')
    parser.add_argument('--quick', action='store_true',
                        help='Quick preview (720p, 2s per preset)')

    args = parser.parse_args()

    if args.quick:
        render_demo_video(
            output_path=args.output,
            width=1280,
            height=720,
            fps=30,
            preset_duration=2.0,
            transition_duration=1.0
        )
    else:
        render_demo_video(
            output_path=args.output,
            width=args.width,
            height=args.height,
            fps=args.fps,
            preset_duration=args.preset_duration,
            transition_duration=args.transition
        )
