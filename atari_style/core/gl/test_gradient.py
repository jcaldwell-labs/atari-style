"""Test script for GLRenderer with animated gradient shader.

This script verifies the GPU rendering pipeline works correctly:
1. Creates headless OpenGL context
2. Loads and compiles test shader
3. Renders animated frames
4. Exports to image or video

Usage:
    python -m atari_style.core.gl.test_gradient --output test.png
    python -m atari_style.core.gl.test_gradient --video test.mp4 --duration 5
"""

import argparse
import sys
import os
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from atari_style.core.gl import GLRenderer, ShaderUniforms


def test_basic_render():
    """Test basic rendering to verify GPU pipeline."""
    print("Testing GLRenderer...")
    print("=" * 50)

    try:
        # Create renderer
        renderer = GLRenderer(width=640, height=480, headless=True)
        info = renderer.get_info()

        print(f"OpenGL Version: {info['version']}")
        print(f"GPU Vendor: {info['vendor']}")
        print(f"GPU Renderer: {info['renderer']}")
        print(f"Max Texture Size: {info['max_texture_size']}")
        print(f"Framebuffer: {info['framebuffer_size']}")
        print()

        # Load test shader
        shader_path = 'atari_style/shaders/effects/test_gradient.frag'
        print(f"Loading shader: {shader_path}")
        program = renderer.load_shader(shader_path)
        print("Shader compiled successfully!")
        print()

        # Test render
        uniforms = ShaderUniforms(
            iTime=0.0,
            iResolution=(640.0, 480.0),
            iParams=(0.8, 0.3, 0.5, 0.5)
        )

        print("Rendering test frame...")
        start = time.perf_counter()
        pixels = renderer.render(program, uniforms.to_dict())
        elapsed = time.perf_counter() - start

        print(f"Rendered {len(pixels)} bytes in {elapsed*1000:.2f}ms")
        print(f"That's {640*480*4} expected bytes (640x480 RGBA)")
        print()

        # Verify we got valid pixel data
        if len(pixels) == 640 * 480 * 4:
            print("SUCCESS: Pixel buffer size matches expected!")
        else:
            print(f"ERROR: Expected {640*480*4} bytes, got {len(pixels)}")
            return False

        renderer.release()
        print("Renderer released successfully.")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def render_to_image(output_path: str, width: int = 1920, height: int = 1080, t: float = 0.0):
    """Render a single frame to an image file."""
    from PIL import Image

    print(f"Rendering {width}x{height} image to {output_path}...")

    with GLRenderer(width=width, height=height, headless=True) as renderer:
        program = renderer.load_shader('atari_style/shaders/effects/test_gradient.frag')

        uniforms = ShaderUniforms(
            iTime=t,
            iResolution=(float(width), float(height)),
            iParams=(0.8, 0.3, 0.5, 0.5)
        )

        # Get as numpy array (already flipped)
        arr = renderer.render_to_array(program, uniforms.to_dict())

        # Create PIL image and save
        img = Image.fromarray(arr, 'RGBA')
        img.save(output_path)

    print(f"Saved to {output_path}")
    file_size = os.path.getsize(output_path)
    print(f"File size: {file_size / 1024:.1f} KB")


def render_to_video(output_path: str, duration: float = 5.0, fps: int = 30,
                    width: int = 1920, height: int = 1080):
    """Render animated frames to video file."""
    import subprocess
    import tempfile
    import shutil
    from PIL import Image

    print(f"Rendering {duration}s video at {fps}fps ({width}x{height})...")
    total_frames = int(duration * fps)

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix='gl_test_')
    print(f"Temp directory: {temp_dir}")

    try:
        with GLRenderer(width=width, height=height, headless=True) as renderer:
            program = renderer.load_shader('atari_style/shaders/effects/test_gradient.frag')

            uniforms = ShaderUniforms(
                iResolution=(float(width), float(height)),
                iParams=(0.8, 0.3, 0.5, 0.5)
            )

            # Render frames
            for i in range(total_frames):
                uniforms.iTime = i / fps

                arr = renderer.render_to_array(program, uniforms.to_dict())
                img = Image.fromarray(arr, 'RGBA')

                # Convert to RGB for video
                img = img.convert('RGB')
                frame_path = os.path.join(temp_dir, f'frame_{i:05d}.png')
                img.save(frame_path)

                if (i + 1) % fps == 0:
                    print(f"  Frame {i + 1}/{total_frames}")

        print(f"\nEncoding video with ffmpeg...")

        # Find ffmpeg
        ffmpeg = 'ffmpeg'
        if sys.platform == 'win32':
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
            '-crf', '18',
            '-preset', 'fast',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            print(f"\nSaved to {output_path}")
            print(f"File size: {file_size / 1024 / 1024:.2f} MB")
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    finally:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir, ignore_errors=True)

    return True


def main():
    parser = argparse.ArgumentParser(description='Test GLRenderer with gradient shader')
    parser.add_argument('--output', '-o', help='Output image path (PNG)')
    parser.add_argument('--video', '-v', help='Output video path (MP4)')
    parser.add_argument('--duration', '-d', type=float, default=5.0,
                        help='Video duration in seconds')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--width', '-W', type=int, default=1920, help='Width in pixels')
    parser.add_argument('--height', '-H', type=int, default=1080, help='Height in pixels')
    parser.add_argument('--time', '-t', type=float, default=1.5,
                        help='Time value for static image')

    args = parser.parse_args()

    # Run basic test first
    if not test_basic_render():
        print("\nBasic test FAILED!")
        sys.exit(1)

    print("\nBasic test PASSED!")
    print()

    # Generate output if requested
    if args.output:
        render_to_image(args.output, args.width, args.height, args.time)
    elif args.video:
        render_to_video(args.video, args.duration, args.fps, args.width, args.height)
    else:
        print("Use --output FILE.png or --video FILE.mp4 to generate output")


if __name__ == '__main__':
    main()
