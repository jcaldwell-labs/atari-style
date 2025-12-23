#!/usr/bin/env python3
"""Phosphor Persistence Demo - CRT phosphor decay visualization.

This demo showcases the phosphor persistence post-processing effect,
which simulates how CRT phosphor coatings continue to glow briefly
after the electron beam moves on.

The effect is most visible on:
- Fast-moving objects (creates motion blur-like trails)
- Bright elements against dark backgrounds
- High-contrast animations like plasma or Lissajous curves

Usage:
    # Interactive mode (requires display)
    python -m atari_style.demos.visualizers.phosphor_demo

    # Export video with phosphor effect
    python -m atari_style.demos.visualizers.phosphor_demo -o phosphor-demo.mp4

    # Compare presets
    python -m atari_style.demos.visualizers.phosphor_demo --preset heavy -o heavy.mp4
    python -m atari_style.demos.visualizers.phosphor_demo --preset subtle -o subtle.mp4

    # Combine with CRT for authentic look
    python -m atari_style.demos.visualizers.phosphor_demo --crt classic --phosphor arcade -o retro.mp4
"""

import os
import sys
import time
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

try:
    import numpy as np
    from PIL import Image
except ImportError:
    np = None
    Image = None

from ...core.gl import GLRenderer
from ...core.gl.pipeline import (
    PostProcessPipeline,
    PHOSPHOR_PRESETS,
    CRT_PRESETS,
    get_phosphor_preset_names,
    get_crt_preset_names,
)


def render_phosphor_demo(
    output_path: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    duration: float = 10.0,
    fps: int = 30,
    phosphor_preset: str = 'classic',
    crt_preset: str = 'off',
    effect: str = 'plasma',
) -> bool:
    """Render a demo video showcasing phosphor persistence.

    Args:
        output_path: Path to output video file (MP4 or GIF)
        width: Video width
        height: Video height
        duration: Duration in seconds
        fps: Frames per second
        phosphor_preset: Phosphor effect preset name
        crt_preset: Optional CRT effect preset (adds scanlines, curvature)
        effect: Base effect shader ('plasma', 'spiral', 'lissajous')

    Returns:
        True if successful
    """
    if np is None or Image is None:
        print("Error: numpy and Pillow are required")
        return False

    # Map effect names to shader paths
    effect_shaders = {
        'plasma': 'atari_style/shaders/effects/plasma.frag',
        'spiral': 'atari_style/shaders/effects/spiral.frag',
        'lissajous': 'atari_style/shaders/effects/lissajous.frag',
        'flux_spiral': 'atari_style/shaders/effects/flux_spiral.frag',
    }

    shader_path = effect_shaders.get(effect, effect_shaders['plasma'])

    print(f"Phosphor Persistence Demo")
    print(f"=" * 50)
    print(f"Resolution: {width}x{height}")
    print(f"Duration: {duration}s @ {fps}fps")
    print(f"Base effect: {effect}")
    print(f"Phosphor preset: {phosphor_preset}")
    print(f"CRT preset: {crt_preset}")
    print()

    # Show preset details
    if phosphor_preset in PHOSPHOR_PRESETS:
        preset = PHOSPHOR_PRESETS[phosphor_preset]
        print(f"Phosphor settings:")
        print(f"  Persistence: {preset.persistence:.2f}")
        print(f"  Glow intensity: {preset.glowIntensity:.2f}")
        print(f"  Color bleed: {preset.colorBleed:.2f}")
        print(f"  Burn-in: {preset.burnIn:.2f}")
        print()

    # Initialize renderer
    renderer = GLRenderer(width=width, height=height, headless=True)

    try:
        # Load base effect shader
        effect_program = renderer.load_shader(shader_path)
    except FileNotFoundError:
        print(f"Error: Shader not found: {shader_path}")
        return False

    # Create post-processing pipeline
    pipeline = PostProcessPipeline(renderer)

    # Add phosphor pass (should come before CRT for authentic look)
    if phosphor_preset != 'off':
        pipeline.add_phosphor_pass(phosphor_preset)
        print(f"Added phosphor pass: {phosphor_preset}")

    # Optionally add CRT pass
    if crt_preset != 'off':
        pipeline.add_crt_pass(crt_preset)
        print(f"Added CRT pass: {crt_preset}")

    print()

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix='phosphor_demo_')
    print(f"Rendering frames to: {temp_dir}")

    try:
        total_frames = int(duration * fps)

        for i in range(total_frames):
            t = i / fps

            # Effect uniforms - create dynamic animation
            effect_uniforms = {
                'iTime': t,
                'iResolution': (float(width), float(height)),
            }

            # Add effect-specific parameters for more dynamic motion
            if effect == 'plasma':
                effect_uniforms.update({
                    'freq_x': 2.0 + 0.5 * np.sin(t * 0.3),
                    'freq_y': 2.0 + 0.5 * np.cos(t * 0.4),
                    'freq_diag': 1.5 + 0.3 * np.sin(t * 0.5),
                    'freq_radial': 2.0 + 0.4 * np.cos(t * 0.35),
                })
            elif effect == 'spiral':
                effect_uniforms.update({
                    'num_spirals': 5.0,
                    'rotation': t * 2.0,  # Fast rotation shows trails well
                    'tightness': 0.3 + 0.1 * np.sin(t * 0.5),
                    'scale': 1.0,
                })
            elif effect == 'lissajous':
                effect_uniforms.update({
                    'freqA': 3.0 + np.sin(t * 0.2),
                    'freqB': 2.0 + np.cos(t * 0.25),
                    'phase': t * 0.5,
                    'points': 500.0,
                })

            # Render with pipeline
            arr = pipeline.render_to_array(effect_program, effect_uniforms, time=t)

            # Save frame
            img = Image.fromarray(arr)
            img.save(os.path.join(temp_dir, f'frame_{i:05d}.png'))

            # Progress
            if (i + 1) % 30 == 0:
                pct = (i + 1) / total_frames * 100
                print(f"  Frame {i+1}/{total_frames} ({pct:.0f}%)")

        # Encode video
        if output_path:
            print(f"\nEncoding video...")

            is_gif = output_path.lower().endswith('.gif')
            frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')

            # Find ffmpeg
            ffmpeg_cmd = shutil.which('ffmpeg') or 'ffmpeg'

            if is_gif:
                # GIF encoding with palette
                palette_path = os.path.join(temp_dir, 'palette.png')
                subprocess.run([
                    ffmpeg_cmd, '-y', '-framerate', str(fps),
                    '-i', frame_pattern,
                    '-vf', 'palettegen=stats_mode=diff',
                    palette_path
                ], capture_output=True)

                result = subprocess.run([
                    ffmpeg_cmd, '-y', '-framerate', str(fps),
                    '-i', frame_pattern, '-i', palette_path,
                    '-lavfi', 'paletteuse=dither=bayer:bayer_scale=5',
                    output_path
                ], capture_output=True, text=True)
            else:
                # MP4 encoding
                result = subprocess.run([
                    ffmpeg_cmd, '-y', '-framerate', str(fps),
                    '-i', frame_pattern,
                    '-c:v', 'libx264', '-preset', 'medium',
                    '-crf', '20', '-pix_fmt', 'yuv420p',
                    output_path
                ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Encoding failed: {result.stderr}")
                return False

            size_kb = os.path.getsize(output_path) / 1024
            print(f"Success! {output_path} ({size_kb:.1f} KB)")
        else:
            print("\nNo output path specified - frames saved to temp directory")
            print(f"Frames: {temp_dir}")
            return True

    finally:
        if output_path:
            shutil.rmtree(temp_dir, ignore_errors=True)
        pipeline.release()

    return True


def print_presets():
    """Print available phosphor presets with descriptions."""
    print("Available phosphor presets:")
    print("-" * 60)
    for name, preset in PHOSPHOR_PRESETS.items():
        print(f"  {name:15s} - persistence={preset.persistence:.2f}, "
              f"glow={preset.glowIntensity:.1f}, "
              f"bleed={preset.colorBleed:.2f}")
    print()
    print("Available CRT presets:")
    print("-" * 60)
    for name in get_crt_preset_names():
        print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(
        description="Phosphor Persistence Demo - CRT phosphor decay effect"
    )

    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output video path (MP4 or GIF)')
    parser.add_argument('--width', type=int, default=1280,
                       help='Video width (default: 1280)')
    parser.add_argument('--height', type=int, default=720,
                       help='Video height (default: 720)')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Duration in seconds (default: 10)')
    parser.add_argument('--fps', type=int, default=30,
                       help='Frames per second (default: 30)')
    parser.add_argument('--phosphor', type=str, default='classic',
                       choices=get_phosphor_preset_names(),
                       help='Phosphor preset (default: classic)')
    parser.add_argument('--crt', type=str, default='off',
                       choices=get_crt_preset_names(),
                       help='CRT preset to combine (default: off)')
    parser.add_argument('--effect', type=str, default='plasma',
                       choices=['plasma', 'spiral', 'lissajous', 'flux_spiral'],
                       help='Base effect shader (default: plasma)')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available presets and exit')

    args = parser.parse_args()

    if args.list_presets:
        print_presets()
        return 0

    success = render_phosphor_demo(
        output_path=args.output,
        width=args.width,
        height=args.height,
        duration=args.duration,
        fps=args.fps,
        phosphor_preset=args.phosphor,
        crt_preset=args.crt,
        effect=args.effect,
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
