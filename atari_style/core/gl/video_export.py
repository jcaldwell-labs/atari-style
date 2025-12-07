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
import tempfile
import shutil
from typing import Optional, Tuple, Callable, Dict

try:
    from PIL import Image
except ImportError:
    Image = None

from .composites import CompositeManager, COMPOSITES
from .pipeline import ASCII_PRESETS, get_ascii_preset_names
from ..video_base import VideoFormat, PresetManager, FFmpegEncoder

# Backward compatibility: alias VIDEO_FORMATS to PresetManager.PRESETS
VIDEO_FORMATS: Dict[str, VideoFormat] = PresetManager.PRESETS


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
        self.encoder = FFmpegEncoder()

    def export_composite(self, composite_name: str, output_path: str,
                         duration: float = 10.0, fps: Optional[int] = None,
                         width: Optional[int] = None, height: Optional[int] = None,
                         params: Optional[Tuple[float, float, float, float]] = None,
                         color_mode: Optional[int] = None,
                         progress_callback: Optional[Callable[[int, int], None]] = None,
                         crf: int = 18,
                         ascii_preset: Optional[str] = None) -> bool:
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
            ascii_preset: ASCII post-processing preset (terminal, hires, lores, neon, colored)

        Returns:
            True if export succeeded, False otherwise

        Raises:
            ValueError: If composite_name is not recognized
            RuntimeError: If ffmpeg is not available
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if not self.encoder.is_available():
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
            if ascii_preset:
                print(f"ASCII preset: {ascii_preset}")
            print(f"Output: {output_path}")
            print()

            # Render frames
            for frame_num in range(total_frames):
                time_val = frame_num / frame_rate

                # Render frame
                img = manager.render_frame(composite_name, time_val, params, color_mode, w, h,
                                           ascii_preset=ascii_preset)

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

            # Encode with shared encoder
            success = self.encoder.encode_video(
                temp_dir,
                output_path,
                frame_rate,
                frame_pattern='frame_%06d.png',
                crf=crf,
            )

            if success:
                size = os.path.getsize(output_path)
                print(f"\nSuccess! Video saved to: {output_path}")
                print(f"File size: {size / 1024 / 1024:.1f} MB")
                return True
            else:
                print(f"Error encoding video")
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
                           crf: Optional[int] = None) -> bool:
        """Export using a predefined format preset.

        Args:
            composite_name: Name of composite to render
            output_path: Output video file path
            format_name: Name of format preset (e.g., 'youtube_shorts', 'tiktok')
            duration: Duration in seconds (uses format max if None and format has limit)
            params: Custom parameters (uses defaults if None)
            color_mode: Color palette (uses default if None)
            crf: FFmpeg CRF quality (uses format's crf if None)

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

        # Use format's CRF if not explicitly specified
        if crf is None:
            crf = fmt.crf

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

    def create_thumbnail(self, composite_name: str, output_path: str,
                         timestamp: float = 0.0,
                         width: Optional[int] = None, height: Optional[int] = None,
                         params: Optional[Tuple[float, float, float, float]] = None,
                         color_mode: Optional[int] = None) -> bool:
        """Create a single thumbnail image at a specific timestamp.

        Args:
            composite_name: Name of composite
            output_path: Output image path (PNG recommended)
            timestamp: Time in seconds to capture
            width: Image width (uses default if None)
            height: Image height (uses default if None)
            params: Custom parameters
            color_mode: Color palette

        Returns:
            True if thumbnail created successfully
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}")

        w = width or self.width
        h = height or self.height

        manager = CompositeManager(w, h)
        img = manager.render_frame(composite_name, timestamp, params, color_mode, w, h)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        img.save(output_path)
        print(f"Thumbnail saved: {output_path}")
        print(f"  Resolution: {w}x{h}")
        print(f"  Timestamp: {timestamp}s")
        return True

    def create_thumbnails(self, composite_name: str, output_dir: str,
                          timestamps: list,
                          width: Optional[int] = None, height: Optional[int] = None,
                          params: Optional[Tuple[float, float, float, float]] = None,
                          color_mode: Optional[int] = None,
                          prefix: Optional[str] = None) -> list:
        """Create multiple thumbnail images at different timestamps.

        Args:
            composite_name: Name of composite
            output_dir: Directory for output images
            timestamps: List of times in seconds to capture
            width: Image width (uses default if None)
            height: Image height (uses default if None)
            params: Custom parameters
            color_mode: Color palette
            prefix: Optional filename prefix (default: composite name)

        Returns:
            List of output file paths
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}")

        w = width or self.width
        h = height or self.height
        file_prefix = prefix or composite_name

        os.makedirs(output_dir, exist_ok=True)
        manager = CompositeManager(w, h)

        output_paths = []
        for ts in timestamps:
            img = manager.render_frame(composite_name, ts, params, color_mode, w, h)
            filename = f"{file_prefix}_{ts:.1f}s.png"
            output_path = os.path.join(output_dir, filename)
            img.save(output_path)
            output_paths.append(output_path)
            print(f"  Saved: {filename}")

        print(f"\nCreated {len(output_paths)} thumbnails in {output_dir}")
        return output_paths

    def create_all_thumbnails(self, output_dir: str, timestamp: float = 0.0,
                              width: Optional[int] = None, height: Optional[int] = None) -> dict:
        """Create thumbnails for all composites at a given timestamp.

        Args:
            output_dir: Directory for output images
            timestamp: Time in seconds to capture
            width: Image width
            height: Image height

        Returns:
            Dict mapping composite names to output paths
        """
        os.makedirs(output_dir, exist_ok=True)
        results = {}

        for composite_name in COMPOSITES:
            output_path = os.path.join(output_dir, f"{composite_name}.png")
            try:
                self.create_thumbnail(composite_name, output_path, timestamp,
                                     width, height)
                results[composite_name] = output_path
            except Exception as e:
                print(f"Error creating thumbnail for {composite_name}: {e}")
                results[composite_name] = None

        return results

    def create_gif(self, composite_name: str, output_path: str,
                   duration: float = 3.0, fps: int = 15,
                   width: int = 480, height: int = 270,
                   params: Optional[Tuple[float, float, float, float]] = None,
                   color_mode: Optional[int] = None,
                   ascii_preset: Optional[str] = None) -> bool:
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
            ascii_preset: ASCII post-processing preset (terminal, hires, lores, neon, colored)

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
            img = manager.render_frame(composite_name, time_val, params, color_mode,
                                        ascii_preset=ascii_preset)
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
Format presets (--format NAME or --list-formats for all):
  Platform:   youtube_shorts, tiktok, instagram_reels, instagram_story, twitter, discord
  YouTube:    youtube_1080p, youtube_720p, youtube_4k
  Quality:    high (1080p60), medium (720p30), low (480p), preview
  Square:     instagram_square (1:1)

Examples:
  %(prog)s plasma_lissajous --shorts
  %(prog)s flux_spiral --format youtube_shorts -d 45
  %(prog)s --all --shorts
  %(prog)s lissajous_plasma --format instagram_reels -o reel.mp4

Quick preview (GIF):
  %(prog)s plasma_lissajous --preview
  %(prog)s flux_spiral --preview --params 0.4,1.5,0.8,0.6 --color 2

ASCII post-processing (terminal aesthetic):
  %(prog)s plasma_lissajous --ascii                    # default terminal preset
  %(prog)s flux_spiral --ascii neon                    # neon ASCII preset
  %(prog)s plasma_lissajous --preview --ascii colored  # preview with colored ASCII

Thumbnails (PNG):
  %(prog)s plasma_lissajous --thumbnail 5.0 -o thumb.png
  %(prog)s flux_spiral --thumbnails 0,2.5,5,7.5 -o ./thumbs/
  %(prog)s --all-thumbnails -o ./all_thumbs/
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
    parser.add_argument('--ascii', '-a', type=str, nargs='?', const='terminal',
                        choices=get_ascii_preset_names(),
                        help='Apply ASCII post-processing (default: terminal). Options: off, terminal, hires, lores, neon, colored')
    parser.add_argument('--all', action='store_true', help='Export all composites')
    parser.add_argument('--list-formats', action='store_true',
                        help='List available format presets')

    # Thumbnail options
    parser.add_argument('--thumbnail', type=float, metavar='TIME',
                        help='Generate single thumbnail at TIME seconds')
    parser.add_argument('--thumbnails', type=str, metavar='T1,T2,...',
                        help='Generate thumbnails at multiple timestamps')
    parser.add_argument('--all-thumbnails', action='store_true',
                        help='Generate thumbnails for all composites')
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

    # Handle thumbnail generation
    if args.all_thumbnails:
        output_dir = args.output or '/tmp/gl_thumbnails'
        timestamp = args.thumbnail if args.thumbnail is not None else 2.0
        print(f"Generating thumbnails for all composites at t={timestamp}s")
        results = exporter.create_all_thumbnails(output_dir, timestamp, width, height)
        print(f"\nGenerated {len([v for v in results.values() if v])} thumbnails in {output_dir}")
        return

    if args.thumbnail is not None and args.composite:
        output_path = args.output or f"/tmp/{args.composite}_{args.thumbnail}s.png"
        exporter.create_thumbnail(args.composite, output_path, args.thumbnail,
                                  width, height, custom_params, args.color)
        return

    if args.thumbnails and args.composite:
        try:
            timestamps = [float(t.strip()) for t in args.thumbnails.split(',')]
        except ValueError as e:
            print(f"Error parsing --thumbnails: {e}")
            return
        output_dir = args.output or f"/tmp/{args.composite}_thumbs"
        exporter.create_thumbnails(args.composite, output_dir, timestamps,
                                   width, height, custom_params, args.color)
        return

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
            if args.ascii:
                print(f"  ASCII preset: {args.ascii}")
            exporter.create_gif(args.composite, output_path, preview_duration,
                               fps=15, width=480, height=270,
                               params=custom_params, color_mode=args.color,
                               ascii_preset=args.ascii)
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
                                      params=custom_params, color_mode=args.color,
                                      ascii_preset=args.ascii)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
