"""GPU-accelerated video export utilities (Phase 5).

Provides video export functionality for GPU-rendered composite animations
using ffmpeg for encoding.

Usage:
    from atari_style.core.gl.video_export import VideoExporter

    # Export a single composite
    exporter = VideoExporter()
    exporter.export_composite('plasma_lissajous', 'output.mp4', duration=10.0)

    # Export with custom settings
    exporter.export_composite('flux_spiral', 'output.mp4',
                              duration=15.0, fps=60, width=1920, height=1080)
"""

import os
import subprocess
import tempfile
import shutil
from typing import Optional, Tuple, Callable

try:
    from PIL import Image
except ImportError:
    Image = None

from .composites import CompositeManager, COMPOSITES


class VideoExporter:
    """Export GPU-rendered composites to video files."""

    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        """Initialize video exporter.

        Args:
            width: Default video width
            height: Default video height
            fps: Default frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self._ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def export_composite(self, composite_name: str, output_path: str,
                         duration: float = 10.0, fps: Optional[int] = None,
                         width: Optional[int] = None, height: Optional[int] = None,
                         params: Optional[Tuple[float, float, float, float]] = None,
                         color_mode: Optional[int] = None,
                         progress_callback: Optional[Callable[[int, int], None]] = None,
                         crf: int = 18) -> bool:
        """Export a composite animation to video.

        Args:
            composite_name: Name of composite to render
            output_path: Output video file path
            duration: Duration in seconds
            fps: Frames per second (uses default if None)
            width: Video width (uses default if None)
            height: Video height (uses default if None)
            params: Custom parameters (uses defaults if None)
            color_mode: Color palette (uses default if None)
            progress_callback: Optional callback(current_frame, total_frames)
            crf: FFmpeg CRF quality (lower = better, 18-28 recommended)

        Returns:
            True if export succeeded, False otherwise

        Raises:
            ValueError: If composite_name is not recognized
            RuntimeError: If ffmpeg is not available
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if not self._ffmpeg_available:
            raise RuntimeError("ffmpeg not found. Install ffmpeg to export videos.")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}. Available: {list(COMPOSITES.keys())}")

        w = width or self.width
        h = height or self.height
        frame_rate = fps or self.fps
        total_frames = int(duration * frame_rate)

        # Create temporary directory for frames
        temp_dir = tempfile.mkdtemp(prefix='gl_composite_')

        try:
            # Initialize manager with target resolution
            manager = CompositeManager(w, h)

            print(f"Rendering {composite_name}: {total_frames} frames at {frame_rate} FPS")
            print(f"Resolution: {w}x{h}")
            print(f"Output: {output_path}")
            print()

            # Render frames
            for frame_num in range(total_frames):
                time_val = frame_num / frame_rate

                # Render frame
                img = manager.render_frame(composite_name, time_val, params, color_mode, w, h)

                # Save frame
                frame_path = os.path.join(temp_dir, f"frame_{frame_num:06d}.png")
                img.save(frame_path, 'PNG')

                # Progress callback
                if progress_callback:
                    progress_callback(frame_num + 1, total_frames)
                elif (frame_num + 1) % 30 == 0:
                    percent = (frame_num + 1) / total_frames * 100
                    print(f"  Frame {frame_num + 1}/{total_frames} ({percent:.0f}%)")

            print(f"\nAll frames rendered. Encoding video...")

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Encode with ffmpeg
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(frame_rate),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', str(crf),
                '-preset', 'medium',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                size = os.path.getsize(output_path)
                print(f"\nSuccess! Video saved to: {output_path}")
                print(f"File size: {size / 1024 / 1024:.1f} MB")
                return True
            else:
                print(f"Error encoding video: {result.stderr}")
                return False

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def export_all_composites(self, output_dir: str, duration: float = 10.0,
                              fps: Optional[int] = None,
                              width: Optional[int] = None,
                              height: Optional[int] = None) -> dict:
        """Export all composite animations to videos.

        Args:
            output_dir: Directory for output videos
            duration: Duration for each video
            fps: Frames per second
            width: Video width
            height: Video height

        Returns:
            Dict mapping composite names to success status
        """
        results = {}

        os.makedirs(output_dir, exist_ok=True)

        for composite_name in COMPOSITES:
            output_path = os.path.join(output_dir, f"{composite_name}.mp4")
            print(f"\n{'=' * 60}")
            print(f"Exporting: {composite_name}")
            print('=' * 60)

            try:
                success = self.export_composite(
                    composite_name, output_path,
                    duration=duration, fps=fps,
                    width=width, height=height
                )
                results[composite_name] = success
            except Exception as e:
                print(f"Error: {e}")
                results[composite_name] = False

        return results

    def export_frames(self, composite_name: str, output_dir: str,
                      duration: float = 5.0, fps: Optional[int] = None,
                      width: Optional[int] = None, height: Optional[int] = None,
                      params: Optional[Tuple[float, float, float, float]] = None,
                      color_mode: Optional[int] = None,
                      format: str = 'png') -> int:
        """Export individual frames (useful for testing or custom encoding).

        Args:
            composite_name: Name of composite
            output_dir: Directory for frame files
            duration: Duration in seconds
            fps: Frames per second
            width: Frame width
            height: Frame height
            params: Custom parameters
            color_mode: Color palette
            format: Image format (png, jpg)

        Returns:
            Number of frames exported
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}")

        w = width or self.width
        h = height or self.height
        frame_rate = fps or self.fps
        total_frames = int(duration * frame_rate)

        os.makedirs(output_dir, exist_ok=True)

        manager = CompositeManager(w, h)

        for frame_num in range(total_frames):
            time_val = frame_num / frame_rate
            img = manager.render_frame(composite_name, time_val, params, color_mode, w, h)

            ext = format.lower()
            frame_path = os.path.join(output_dir, f"frame_{frame_num:06d}.{ext}")
            img.save(frame_path, format.upper())

        return total_frames

    def create_gif(self, composite_name: str, output_path: str,
                   duration: float = 3.0, fps: int = 15,
                   width: int = 480, height: int = 270,
                   params: Optional[Tuple[float, float, float, float]] = None,
                   color_mode: Optional[int] = None) -> bool:
        """Create an animated GIF of a composite.

        Args:
            composite_name: Name of composite
            output_path: Output GIF path
            duration: Duration in seconds
            fps: Frames per second (lower for smaller file)
            width: GIF width (smaller for smaller file)
            height: GIF height
            params: Custom parameters
            color_mode: Color palette

        Returns:
            True if GIF created successfully
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}")

        manager = CompositeManager(width, height)
        total_frames = int(duration * fps)

        frames = []
        for frame_num in range(total_frames):
            time_val = frame_num / fps
            img = manager.render_frame(composite_name, time_val, params, color_mode)
            # Convert to RGB for GIF (remove alpha)
            frames.append(img.convert('RGB'))

        # Save as animated GIF
        frame_duration = int(1000 / fps)  # milliseconds per frame
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=0
        )

        print(f"GIF saved to: {output_path}")
        print(f"Size: {os.path.getsize(output_path) / 1024:.1f} KB")

        return True


def export_composite_video(composite_name: str, output_path: str,
                           duration: float = 10.0, **kwargs) -> bool:
    """Convenience function to export a single composite.

    Args:
        composite_name: Name of the composite
        output_path: Output video path
        duration: Duration in seconds
        **kwargs: Additional arguments passed to VideoExporter.export_composite

    Returns:
        True if export succeeded
    """
    exporter = VideoExporter()
    return exporter.export_composite(composite_name, output_path, duration, **kwargs)


def main():
    """Command-line interface for video export."""
    import argparse

    parser = argparse.ArgumentParser(description='Export GPU composite animations to video')
    parser.add_argument('composite', nargs='?', choices=list(COMPOSITES.keys()),
                        help='Composite to export (omit for all)')
    parser.add_argument('-o', '--output', help='Output path (or directory for --all)')
    parser.add_argument('-d', '--duration', type=float, default=10.0,
                        help='Duration in seconds')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--width', type=int, default=1280, help='Video width')
    parser.add_argument('--height', type=int, default=720, help='Video height')
    parser.add_argument('--gif', action='store_true', help='Export as GIF instead')
    parser.add_argument('--all', action='store_true', help='Export all composites')
    args = parser.parse_args()

    exporter = VideoExporter(args.width, args.height, args.fps)

    if args.all:
        output_dir = args.output or '/tmp/gl_composites'
        results = exporter.export_all_composites(output_dir, args.duration,
                                                  args.fps, args.width, args.height)
        print("\nSummary:")
        for name, success in results.items():
            status = "OK" if success else "FAILED"
            print(f"  {name}: {status}")

    elif args.composite:
        if args.gif:
            output_path = args.output or f"/tmp/{args.composite}.gif"
            exporter.create_gif(args.composite, output_path, args.duration,
                               fps=min(args.fps, 15), width=480, height=270)
        else:
            output_path = args.output or f"/tmp/{args.composite}.mp4"
            exporter.export_composite(args.composite, output_path, args.duration,
                                      args.fps, args.width, args.height)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
