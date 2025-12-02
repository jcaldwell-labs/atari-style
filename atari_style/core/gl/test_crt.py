"""Test script for CRT post-processing pipeline.

Demonstrates the CRT and palette reduction effects applied to
the GPU Mandelbrot visualizer.

Usage:
    python -m atari_style.core.gl.test_crt
    python -m atari_style.core.gl.test_crt --preset heavy
    python -m atari_style.core.gl.test_crt --output crt_demo.png
    python -m atari_style.core.gl.test_crt --video crt_demo.mp4 --duration 10
"""

import os
import sys
import time
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("ERROR: Pillow and numpy required: pip install Pillow numpy")
    sys.exit(1)

from .renderer import GLRenderer
from .uniforms import ShaderUniforms
from .pipeline import (
    PostProcessPipeline,
    CRT_PRESETS,
    PALETTE_PRESETS,
    get_crt_preset_names,
    get_palette_preset_names,
)


def test_crt_pipeline():
    """Test basic CRT pipeline functionality."""
    print("Testing CRT Post-Processing Pipeline")
    print("=" * 50)

    # Create renderer
    renderer = GLRenderer(width=640, height=480, headless=True)
    info = renderer.get_info()
    print(f"OpenGL Version: {info['version']}")
    print(f"GPU: {info['renderer']}")
    print(f"Software rendering: {info['using_software_rendering']}")

    # Load Mandelbrot shader
    shader_path = 'atari_style/shaders/effects/mandelbrot.frag'
    program = renderer.load_shader(shader_path)
    print(f"\nLoaded effect shader: {shader_path}")

    # Create pipeline with CRT effect
    pipeline = PostProcessPipeline(renderer)
    pipeline.add_crt_pass('classic')
    print(f"Added CRT pass: classic preset")

    # Setup uniforms
    uniforms = ShaderUniforms(iResolution=(640.0, 480.0))
    uniforms.iParams = (1.0, -0.5, 0.0, 100.0)  # zoom, centerX, centerY, iterations
    uniforms.iTime = 0.0
    uniforms.iColorMode = 0

    # Render with CRT
    print("\nRendering test frame with CRT...")
    start = time.time()
    pixels = pipeline.render(program, uniforms.to_dict(), time=0.5)
    elapsed = (time.time() - start) * 1000
    print(f"Rendered {len(pixels)} bytes in {elapsed:.2f}ms")

    # Test all CRT presets
    print("\nTesting CRT presets:")
    for preset_name in get_crt_preset_names():
        pipeline.set_crt_preset(preset_name)
        start = time.time()
        pipeline.render(program, uniforms.to_dict(), time=0.5)
        elapsed = (time.time() - start) * 1000
        preset = CRT_PRESETS[preset_name]
        print(f"  {preset_name:10s}: {elapsed:.2f}ms (scanlines={preset.scanlineIntensity}, curve={preset.curvature})")

    # Cleanup
    pipeline.release()
    renderer.release()

    print("\nTest PASSED!")


def render_comparison_image(
    output_path: str,
    width: int = 1920,
    height: int = 1080
):
    """Render a comparison showing effect with different CRT presets."""
    print(f"Rendering comparison image ({width}x{height})...")

    # Create renderer
    renderer = GLRenderer(width=width//2, height=height//2, headless=True)
    program = renderer.load_shader('atari_style/shaders/effects/mandelbrot.frag')

    # Setup uniforms - interesting Mandelbrot location
    uniforms = ShaderUniforms(iResolution=(width/2, height/2))
    uniforms.iParams = (50.0, -0.743643887037151, 0.131825904205330, 150.0)
    uniforms.iTime = 1.0
    uniforms.iColorMode = 2  # Rainbow

    # Render grid of presets
    presets = ['off', 'subtle', 'classic', 'heavy']
    images = []

    for preset in presets:
        pipeline = PostProcessPipeline(renderer)
        if preset != 'off':
            pipeline.add_crt_pass(preset)

        arr = pipeline.render_to_array(program, uniforms.to_dict(), time=1.0)
        img = Image.fromarray(arr, 'RGBA').convert('RGB')
        images.append((preset, img))
        pipeline.release()

    renderer.release()

    # Create comparison grid
    grid = Image.new('RGB', (width, height))

    # Place images in 2x2 grid
    positions = [(0, 0), (width//2, 0), (0, height//2), (width//2, height//2)]
    for (preset, img), (x, y) in zip(images, positions):
        grid.paste(img, (x, y))

    # Add labels (simple overlay)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(grid)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()

    labels = ['No CRT', 'Subtle', 'Classic', 'Heavy']
    for label, (x, y) in zip(labels, positions):
        # Draw text with shadow for visibility
        draw.text((x + 12, y + 12), label, fill=(0, 0, 0), font=font)
        draw.text((x + 10, y + 10), label, fill=(255, 255, 255), font=font)

    grid.save(output_path)
    print(f"Saved comparison: {output_path}")


def render_crt_video(
    output_path: str,
    crt_preset: str = 'classic',
    palette_preset: str = None,
    width: int = 1920,
    height: int = 1080,
    duration: float = 10.0,
    fps: int = 30
):
    """Render a video with CRT effects."""
    print(f"Rendering CRT video: {output_path}")
    print(f"  Resolution: {width}x{height} @ {fps}fps")
    print(f"  Duration: {duration}s")
    print(f"  CRT preset: {crt_preset}")
    if palette_preset:
        print(f"  Palette: {palette_preset}")

    # Create renderer and pipeline
    renderer = GLRenderer(width=width, height=height, headless=True)
    program = renderer.load_shader('atari_style/shaders/effects/mandelbrot.frag')

    pipeline = PostProcessPipeline(renderer)
    pipeline.add_crt_pass(crt_preset)
    if palette_preset:
        pipeline.add_palette_pass(palette_preset)

    # Animation: zoom into Seahorse Valley
    start_zoom = 1.0
    end_zoom = 200.0
    center_x, center_y = -0.743643887037151, 0.131825904205330

    uniforms = ShaderUniforms(iResolution=(float(width), float(height)))

    temp_dir = tempfile.mkdtemp(prefix='crt_video_')
    num_frames = int(duration * fps)

    try:
        print(f"\nRendering {num_frames} frames...")

        for i in range(num_frames):
            t = i / num_frames
            # Exponential zoom interpolation
            import math
            zoom = math.exp(math.log(start_zoom) + (math.log(end_zoom) - math.log(start_zoom)) * t)

            uniforms.iParams = (zoom, center_x, center_y, 150.0)
            uniforms.iTime = i / fps
            uniforms.iColorMode = 0

            arr = pipeline.render_to_array(program, uniforms.to_dict(), time=uniforms.iTime)
            img = Image.fromarray(arr, 'RGBA').convert('RGB')

            frame_path = os.path.join(temp_dir, f'frame_{i:05d}.png')
            img.save(frame_path)

            if (i + 1) % fps == 0:
                print(f"  {i + 1}/{num_frames} frames ({(i + 1) / num_frames * 100:.0f}%)")

        # Encode with ffmpeg
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg is None:
            print("ERROR: ffmpeg not found")
            return False

        print("\nEncoding video...")
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
        pipeline.release()
        renderer.release()
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description='Test CRT post-processing')
    parser.add_argument('--test', action='store_true', help='Run basic tests')
    parser.add_argument('--output', '-o', help='Save single image to path')
    parser.add_argument('--comparison', '-c', help='Save preset comparison image')
    parser.add_argument('--video', '-v', help='Render video to path')
    parser.add_argument('--preset', '-p', default='classic',
                        choices=get_crt_preset_names(),
                        help='CRT preset to use')
    parser.add_argument('--palette', default=None,
                        choices=get_palette_preset_names(),
                        help='Palette preset (optional)')
    parser.add_argument('--duration', '-d', type=float, default=10.0,
                        help='Video duration in seconds')
    parser.add_argument('--width', '-W', type=int, default=1920)
    parser.add_argument('--height', '-H', type=int, default=1080)
    parser.add_argument('--list-presets', action='store_true',
                        help='List available presets')

    args = parser.parse_args()

    if args.list_presets:
        print("CRT Presets:")
        for name, preset in CRT_PRESETS.items():
            print(f"  {name:10s} - scanlines={preset.scanlineIntensity}, "
                  f"curve={preset.curvature}, vignette={preset.vignetteStrength}")
        print("\nPalette Presets:")
        for name, preset in PALETTE_PRESETS.items():
            print(f"  {name:10s} - levels={preset.colorLevels}, dither={preset.dithering}")
        return

    if args.test or (not args.output and not args.comparison and not args.video):
        test_crt_pipeline()
    elif args.comparison:
        render_comparison_image(args.comparison, args.width, args.height)
    elif args.video:
        render_crt_video(
            args.video,
            crt_preset=args.preset,
            palette_preset=args.palette,
            width=args.width,
            height=args.height,
            duration=args.duration
        )
    elif args.output:
        # Render single image with CRT
        renderer = GLRenderer(width=args.width, height=args.height, headless=True)
        program = renderer.load_shader('atari_style/shaders/effects/mandelbrot.frag')

        pipeline = PostProcessPipeline(renderer)
        pipeline.add_crt_pass(args.preset)
        if args.palette:
            pipeline.add_palette_pass(args.palette)

        uniforms = ShaderUniforms(iResolution=(float(args.width), float(args.height)))
        uniforms.iParams = (50.0, -0.743643887037151, 0.131825904205330, 150.0)
        uniforms.iTime = 1.0
        uniforms.iColorMode = 2

        arr = pipeline.render_to_array(program, uniforms.to_dict(), time=1.0)
        img = Image.fromarray(arr, 'RGBA')
        img.save(args.output)
        print(f"Saved: {args.output}")

        pipeline.release()
        renderer.release()


if __name__ == '__main__':
    main()
