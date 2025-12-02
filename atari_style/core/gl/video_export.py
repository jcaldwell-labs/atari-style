"""GPU-accelerated video export utilities (Phase 5).

Provides video export functionality for GPU-rendered composite animations
using ffmpeg for encoding.

Usage:
    from atari_style.core.gl.video_export import VideoExporter, VIDEO_FORMATS

    # Export a single composite
    exporter = VideoExporter()
    exporter.export_composite('plasma_lissajous', 'output.mp4', duration=10.0)

    # Export with custom settings
    exporter.export_composite('flux_spiral', 'output.mp4',
                              duration=15.0, fps=60, width=1920, height=1080)

    # Export YouTube Shorts (vertical 9:16)
    exporter.export_shorts('plasma_lissajous', 'shorts.mp4', duration=45.0)

    # Use format presets
    fmt = VIDEO_FORMATS['youtube_shorts']
    exporter.export_composite('flux_spiral', 'output.mp4',
                              width=fmt.width, height=fmt.height, fps=fmt.fps)
"""

# Suppress runpy RuntimeWarning when running as __main__
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, module='runpy')

import os
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional, Tuple, Callable, Dict

try:
    from PIL import Image
except ImportError:
    Image = None

from .composites import CompositeManager, COMPOSITES


@dataclass
class VideoFormat:
    """Video format preset configuration."""
    name: str
    width: int
    height: int
    fps: int
    max_duration: Optional[float]  # Platform limit in seconds, None = unlimited
    description: str

    @property
    def aspect_ratio(self) -> str:
        """Return aspect ratio as string (e.g., '16:9', '9:16')."""
        from math import gcd
        g = gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"

    @property
    def is_vertical(self) -> bool:
        """Return True if format is vertical (portrait)."""
        return self.height > self.width


# Common video format presets
VIDEO_FORMATS: Dict[str, VideoFormat] = {
    # Vertical formats (9:16)
    'youtube_shorts': VideoFormat(
        name='YouTube Shorts',
        width=1080,
        height=1920,
        fps=30,
        max_duration=60.0,
        description='YouTube Shorts vertical format (9:16)'
    ),
    'tiktok': VideoFormat(
        name='TikTok',
        width=1080,
        height=1920,
        fps=30,
        max_duration=180.0,  # 3 minutes
        description='TikTok vertical format (9:16)'
    ),
    'instagram_reels': VideoFormat(
        name='Instagram Reels',
        width=1080,
        height=1920,
        fps=30,
        max_duration=90.0,
        description='Instagram Reels vertical format (9:16)'
    ),
    'instagram_story': VideoFormat(
        name='Instagram Story',
        width=1080,
        height=1920,
        fps=30,
        max_duration=15.0,
        description='Instagram Story vertical format (9:16)'
    ),

    # Horizontal formats (16:9)
    'youtube_1080p': VideoFormat(
        name='YouTube 1080p',
        width=1920,
        height=1080,
        fps=30,
        max_duration=None,
        description='Standard YouTube HD format (16:9)'
    ),
    'youtube_4k': VideoFormat(
        name='YouTube 4K',
        width=3840,
        height=2160,
        fps=30,
        max_duration=None,
        description='YouTube 4K UHD format (16:9)'
    ),
    'youtube_720p': VideoFormat(
        name='YouTube 720p',
        width=1280,
        height=720,
        fps=30,
        max_duration=None,
        description='YouTube HD Ready format (16:9)'
    ),

    # Square format (1:1)
    'instagram_square': VideoFormat(
        name='Instagram Square',
        width=1080,
        height=1080,
        fps=30,
        max_duration=60.0,
        description='Instagram square format (1:1)'
    ),
}


def get_format_names() -> list:
    """Get list of available format preset names."""
    return list(VIDEO_FORMATS.keys())


def get_vertical_formats() -> Dict[str, VideoFormat]:
    """Get only vertical format presets."""
    return {k: v for k, v in VIDEO_FORMATS.items() if v.is_vertical}


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

    def export_with_format(self, composite_name: str, output_path: str,
                           format_name: str, duration: Optional[float] = None,
                           params: Optional[Tuple[float, float, float, float]] = None,
                           color_mode: Optional[int] = None,
                           crf: int = 18) -> bool:
        """Export using a predefined format preset.

        Args:
            composite_name: Name of composite to render
            output_path: Output video file path
            format_name: Name of format preset (e.g., 'youtube_shorts', 'tiktok')
            duration: Duration in seconds (uses format max if None and format has limit)
            params: Custom parameters (uses defaults if None)
            color_mode: Color palette (uses default if None)
            crf: FFmpeg CRF quality

        Returns:
            True if export succeeded

        Raises:
            ValueError: If format_name is not recognized
        """
        if format_name not in VIDEO_FORMATS:
            raise ValueError(f"Unknown format: {format_name}. Available: {get_format_names()}")

        fmt = VIDEO_FORMATS[format_name]

        # Use format's max duration if not specified and format has a limit
        if duration is None:
            duration = fmt.max_duration if fmt.max_duration else 10.0

        # Warn if duration exceeds platform limit
        if fmt.max_duration and duration > fmt.max_duration:
            print(f"Warning: Duration {duration}s exceeds {fmt.name} limit of {fmt.max_duration}s")

        print(f"Format: {fmt.name} ({fmt.width}x{fmt.height}, {fmt.aspect_ratio})")

        return self.export_composite(
            composite_name, output_path,
            duration=duration,
            fps=fmt.fps,
            width=fmt.width,
            height=fmt.height,
            params=params,
            color_mode=color_mode,
            crf=crf
        )

    def export_shorts(self, composite_name: str, output_path: str,
                      duration: float = 45.0,
                      params: Optional[Tuple[float, float, float, float]] = None,
                      color_mode: Optional[int] = None,
                      crf: int = 18) -> bool:
        """Export optimized for YouTube Shorts (1080x1920, 9:16 vertical).

        Args:
            composite_name: Name of composite to render
            output_path: Output video file path
            duration: Duration in seconds (max 60s for Shorts)
            params: Custom parameters
            color_mode: Color palette
            crf: FFmpeg CRF quality

        Returns:
            True if export succeeded
        """
        # Duration validation handled by export_with_format via format's max_duration
        return self.export_with_format(
            composite_name, output_path,
            format_name='youtube_shorts',
            duration=duration,
            params=params,
            color_mode=color_mode,
            crf=crf
        )

    def export_all_shorts(self, output_dir: str, duration: float = 45.0) -> dict:
        """Export all composites as YouTube Shorts.

        Args:
            output_dir: Directory for output videos
            duration: Duration for each video (max 60s)

        Returns:
            Dict mapping composite names to success status
        """
        results = {}
        os.makedirs(output_dir, exist_ok=True)

        for composite_name in COMPOSITES:
            output_path = os.path.join(output_dir, f"{composite_name}_short.mp4")
            print(f"\n{'=' * 60}")
            print(f"Exporting Short: {composite_name}")
            print('=' * 60)

            try:
                success = self.export_shorts(composite_name, output_path, duration)
                results[composite_name] = success
            except Exception as e:
                print(f"Error: {e}")
                results[composite_name] = False

        return results

    def export_all_with_format(self, output_dir: str, format_name: str,
                               duration: Optional[float] = None) -> dict:
        """Export all composites using a format preset.

        Args:
            output_dir: Directory for output videos
            format_name: Format preset name (e.g., 'instagram_reels', 'tiktok')
            duration: Duration for each video (uses format default if None)

        Returns:
            Dict mapping composite names to success status
        """
        if format_name not in VIDEO_FORMATS:
            raise ValueError(f"Unknown format: {format_name}")

        fmt = VIDEO_FORMATS[format_name]
        results = {}
        os.makedirs(output_dir, exist_ok=True)

        for composite_name in COMPOSITES:
            output_path = os.path.join(output_dir, f"{composite_name}_{format_name}.mp4")
            print(f"\n{'=' * 60}")
            print(f"Exporting ({fmt.name}): {composite_name}")
            print('=' * 60)

            try:
                success = self.export_with_format(
                    composite_name, output_path, format_name, duration
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
                      image_format: str = 'png') -> int:
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
            image_format: Image format (png, jpg)

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

            ext = image_format.lower()
            frame_path = os.path.join(output_dir, f"frame_{frame_num:06d}.{ext}")
            img.save(frame_path, image_format.upper())

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

    parser = argparse.ArgumentParser(
        description='Export GPU composite animations to video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Format presets:
  youtube_shorts    1080x1920  9:16  (max 60s)
  tiktok            1080x1920  9:16  (max 180s)
  instagram_reels   1080x1920  9:16  (max 90s)
  instagram_story   1080x1920  9:16  (max 15s)
  instagram_square  1080x1080  1:1   (max 60s)
  youtube_1080p     1920x1080  16:9
  youtube_720p      1280x720   16:9
  youtube_4k        3840x2160  16:9

Examples:
  %(prog)s plasma_lissajous --shorts
  %(prog)s flux_spiral --format youtube_shorts -d 45
  %(prog)s --all --shorts
  %(prog)s lissajous_plasma --format instagram_reels -o reel.mp4

Quick preview (GIF):
  %(prog)s plasma_lissajous --preview
  %(prog)s flux_spiral --preview --params 0.4,1.5,0.8,0.6 --color 2
"""
    )
    parser.add_argument('composite', nargs='?', choices=list(COMPOSITES.keys()),
                        help='Composite to export (omit for all)')
    parser.add_argument('-o', '--output', help='Output path (or directory for --all)')
    parser.add_argument('-d', '--duration', type=float,
                        help='Duration in seconds (default: 10s or format max)')
    parser.add_argument('--fps', type=int, help='Frames per second (default: 30)')
    parser.add_argument('--width', type=int, help='Video width')
    parser.add_argument('--height', type=int, help='Video height')

    # Format options (mutually exclusive)
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument('--format', '-f', choices=get_format_names(),
                              help='Use a format preset (overrides width/height/fps)')
    format_group.add_argument('--shorts', action='store_true',
                              help='Export as YouTube Shorts (1080x1920, 9:16)')

    parser.add_argument('--gif', action='store_true', help='Export as GIF instead')
    parser.add_argument('--preview', action='store_true',
                        help='Quick GIF preview (3s, 480x270, 15fps)')
    parser.add_argument('--params', '-p', type=str,
                        help='Custom params as comma-separated floats (e.g., 0.2,0.5,0.7,0.3)')
    parser.add_argument('--color', '-c', type=int, choices=[0, 1, 2, 3],
                        help='Color mode (0=aurora, 1=fire, 2=electric, 3=grayscale)')
    parser.add_argument('--all', action='store_true', help='Export all composites')
    parser.add_argument('--list-formats', action='store_true',
                        help='List available format presets')
    args = parser.parse_args()

    # List formats and exit
    if args.list_formats:
        print("Available video format presets:\n")
        for name, fmt in VIDEO_FORMATS.items():
            limit = f"max {fmt.max_duration}s" if fmt.max_duration else "unlimited"
            print(f"  {name:20} {fmt.width}x{fmt.height}  {fmt.aspect_ratio:5}  ({limit})")
        return

    # Parse custom params if provided
    custom_params = None
    if args.params:
        try:
            custom_params = tuple(float(x.strip()) for x in args.params.split(','))
            if len(custom_params) != 4:
                print(f"Error: --params requires exactly 4 values, got {len(custom_params)}")
                return
        except ValueError as e:
            print(f"Error parsing --params: {e}")
            return

    # Determine format name for format-based exports
    format_name = 'youtube_shorts' if args.shorts else args.format

    # Determine format settings
    if format_name:
        fmt = VIDEO_FORMATS[format_name]
        width = fmt.width
        height = fmt.height
        fps = fmt.fps
        duration = args.duration or (fmt.max_duration if fmt.max_duration else 10.0)
    else:
        width = args.width or 1280
        height = args.height or 720
        fps = args.fps or 30
        duration = args.duration or 10.0

    exporter = VideoExporter(width, height, fps)

    if args.all:
        if format_name:
            output_dir = args.output or f'/tmp/gl_{format_name}'
            results = exporter.export_all_with_format(output_dir, format_name, duration)
        else:
            output_dir = args.output or '/tmp/gl_composites'
            results = exporter.export_all_composites(output_dir, duration,
                                                      fps, width, height)
        print("\nSummary:")
        for name, success in results.items():
            status = "OK" if success else "FAILED"
            print(f"  {name}: {status}")

    elif args.composite:
        if args.preview:
            # Quick preview: 3s GIF at low resolution
            import time as time_mod
            timestamp = int(time_mod.time()) % 10000
            output_path = args.output or f"/tmp/{args.composite}_preview_{timestamp}.gif"
            preview_duration = args.duration or 3.0
            print(f"Quick preview: {args.composite}")
            if custom_params:
                print(f"  Params: {custom_params}")
            if args.color is not None:
                print(f"  Color mode: {args.color}")
            exporter.create_gif(args.composite, output_path, preview_duration,
                               fps=15, width=480, height=270,
                               params=custom_params, color_mode=args.color)
        elif args.gif:
            output_path = args.output or f"/tmp/{args.composite}.gif"
            exporter.create_gif(args.composite, output_path, duration,
                               fps=min(fps, 15), width=480, height=270,
                               params=custom_params, color_mode=args.color)
        elif format_name:
            output_path = args.output or f"/tmp/{args.composite}_{format_name}.mp4"
            exporter.export_with_format(args.composite, output_path, format_name, duration,
                                        params=custom_params, color_mode=args.color)
        else:
            output_path = args.output or f"/tmp/{args.composite}.mp4"
            exporter.export_composite(args.composite, output_path, duration,
                                      fps, width, height,
                                      params=custom_params, color_mode=args.color)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
