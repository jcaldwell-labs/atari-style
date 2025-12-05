"""Unified video export base classes and utilities.

Provides shared infrastructure for both GL and terminal video export pipelines:
- VideoExporter: Abstract base class for video exporters
- FFmpegEncoder: Shared ffmpeg encoding logic
- ProgressReporter: Progress reporting utilities
- PresetManager: Resolution and format preset management

This module consolidates common patterns from gl/video_export.py and demo_video.py
to provide a unified video export architecture.
"""

import os
import subprocess
import tempfile
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List


@dataclass
class VideoFormat:
    """Video format preset configuration."""
    name: str
    width: int
    height: int
    fps: int
    max_duration: Optional[float] = None  # Platform limit in seconds
    description: str = ""
    crf: int = 23  # FFmpeg quality (lower = better, 18-28 recommended)

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

    @property
    def is_square(self) -> bool:
        """Return True if format is square."""
        return self.width == self.height


class FFmpegEncoder:
    """Shared ffmpeg encoding logic for video export."""

    def __init__(self):
        """Initialize encoder and check ffmpeg availability."""
        self._ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_available(self) -> bool:
        """Check if ffmpeg is available for encoding."""
        return self._ffmpeg_available

    def encode_video(
        self,
        frames_dir: str,
        output_path: str,
        fps: int,
        frame_pattern: str = 'frame_%05d.png',
        crf: int = 23,
        preset: str = 'medium',
        pix_fmt: str = 'yuv420p',
        codec: str = 'libx264',
    ) -> bool:
        """Encode frames to MP4 video using ffmpeg.

        Args:
            frames_dir: Directory containing frame images
            output_path: Output video file path
            fps: Frames per second
            frame_pattern: Frame filename pattern (default: frame_%05d.png)
            crf: Constant Rate Factor (18=high quality, 28=lower quality)
            preset: Encoding preset (ultrafast, fast, medium, slow, veryslow)
            pix_fmt: Pixel format (yuv420p for compatibility)
            codec: Video codec (libx264 for H.264)

        Returns:
            True if encoding succeeded, False otherwise

        Raises:
            RuntimeError: If ffmpeg is not available
        """
        if not self._ffmpeg_available:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        frame_path = os.path.join(frames_dir, frame_pattern)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(fps),
            '-i', frame_path,
            '-c:v', codec,
            '-pix_fmt', pix_fmt,
            '-crf', str(crf),
            '-preset', preset,
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    def encode_gif(
        self,
        frames_dir: str,
        output_path: str,
        fps: int,
        frame_pattern: str = 'frame_%05d.png',
        scale: int = 480,
        colors: int = 256,
    ) -> bool:
        """Encode frames to animated GIF using ffmpeg.

        Args:
            frames_dir: Directory containing frame images
            output_path: Output GIF file path
            fps: Frames per second
            frame_pattern: Frame filename pattern
            scale: Maximum width in pixels (maintains aspect ratio)
            colors: Number of colors in palette (max 256)

        Returns:
            True if encoding succeeded, False otherwise

        Raises:
            RuntimeError: If ffmpeg is not available
        """
        if not self._ffmpeg_available:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        frame_path = os.path.join(frames_dir, frame_pattern)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Two-pass GIF encoding for better quality
        palette_path = os.path.join(frames_dir, 'palette.png')

        # Generate palette
        palette_cmd = [
            'ffmpeg',
            '-y',
            '-i', frame_path,
            '-vf', f'fps={fps},scale={scale}:-1:flags=lanczos,palettegen=max_colors={colors}',
            palette_path
        ]

        result = subprocess.run(palette_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Palette generation error: {result.stderr}")
            return False

        # Generate GIF using palette
        gif_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(fps),
            '-i', frame_path,
            '-i', palette_path,
            '-filter_complex', f'fps={fps},scale={scale}:-1:flags=lanczos[x];[x][1:v]paletteuse',
            output_path
        ]

        result = subprocess.run(gif_cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True
        else:
            print(f"GIF encoding error: {result.stderr}")
            return False


class ProgressReporter:
    """Progress reporting for video export operations."""

    def __init__(
        self,
        total_frames: int,
        callback: Optional[Callable[[int, int], None]] = None,
        report_interval: int = 30,
    ):
        """Initialize progress reporter.

        Args:
            total_frames: Total number of frames to render
            callback: Optional callback(current_frame, total_frames)
            report_interval: Report progress every N frames (default: 30)
        """
        self.total_frames = total_frames
        self.callback = callback
        self.report_interval = report_interval
        self.current_frame = 0

    def update(self, frame_num: Optional[int] = None):
        """Update progress.

        Args:
            frame_num: Current frame number (auto-increments if None)
        """
        if frame_num is not None:
            self.current_frame = frame_num
        else:
            self.current_frame += 1

        # Call custom callback
        if self.callback:
            self.callback(self.current_frame, self.total_frames)

        # Default console reporting
        elif self.current_frame % self.report_interval == 0 or self.current_frame == self.total_frames:
            percent = (self.current_frame / self.total_frames) * 100
            print(f"  Frame {self.current_frame}/{self.total_frames} ({percent:.0f}%)")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None and self.current_frame == self.total_frames:
            print(f"\n✓ Rendered {self.total_frames} frames")
        return False


class PresetManager:
    """Manages video format presets and resolution configurations."""

    # Standard video format presets
    PRESETS: Dict[str, VideoFormat] = {
        # Vertical formats (9:16)
        'youtube_shorts': VideoFormat(
            name='YouTube Shorts',
            width=1080,
            height=1920,
            fps=30,
            max_duration=60.0,
            description='YouTube Shorts vertical format (9:16)',
            crf=23,
        ),
        'tiktok': VideoFormat(
            name='TikTok',
            width=1080,
            height=1920,
            fps=30,
            max_duration=180.0,
            description='TikTok vertical format (9:16)',
            crf=23,
        ),
        'instagram_reels': VideoFormat(
            name='Instagram Reels',
            width=1080,
            height=1920,
            fps=30,
            max_duration=90.0,
            description='Instagram Reels vertical format (9:16)',
            crf=23,
        ),
        'instagram_story': VideoFormat(
            name='Instagram Story',
            width=1080,
            height=1920,
            fps=30,
            max_duration=15.0,
            description='Instagram Story vertical format (9:16)',
            crf=23,
        ),

        # Horizontal formats (16:9)
        'youtube_1080p': VideoFormat(
            name='YouTube 1080p',
            width=1920,
            height=1080,
            fps=30,
            max_duration=None,
            description='Standard YouTube HD format (16:9)',
            crf=23,
        ),
        'youtube_4k': VideoFormat(
            name='YouTube 4K',
            width=3840,
            height=2160,
            fps=30,
            max_duration=None,
            description='YouTube 4K UHD format (16:9)',
            crf=18,
        ),
        'youtube_720p': VideoFormat(
            name='YouTube 720p',
            width=1280,
            height=720,
            fps=30,
            max_duration=None,
            description='YouTube HD Ready format (16:9)',
            crf=23,
        ),

        # Square format (1:1)
        'instagram_square': VideoFormat(
            name='Instagram Square',
            width=1080,
            height=1080,
            fps=30,
            max_duration=60.0,
            description='Instagram square format (1:1)',
            crf=23,
        ),

        # Quality presets
        'high': VideoFormat(
            name='High Quality',
            width=1920,
            height=1080,
            fps=60,
            max_duration=None,
            description='High quality 1080p60 (large files)',
            crf=18,
        ),
        'medium': VideoFormat(
            name='Medium Quality',
            width=1280,
            height=720,
            fps=30,
            max_duration=None,
            description='Medium quality 720p30 (balanced)',
            crf=23,
        ),
        'low': VideoFormat(
            name='Low Quality',
            width=854,
            height=480,
            fps=30,
            max_duration=None,
            description='Low quality 480p (small files)',
            crf=28,
        ),
        'preview': VideoFormat(
            name='Preview',
            width=480,
            height=270,
            fps=15,
            max_duration=None,
            description='Quick preview (very small files)',
            crf=28,
        ),

        # Social media
        'twitter': VideoFormat(
            name='Twitter/X',
            width=1280,
            height=720,
            fps=30,
            max_duration=140.0,
            description='Twitter/X video (720p, max 2:20)',
            crf=23,
        ),
        'discord': VideoFormat(
            name='Discord',
            width=1280,
            height=720,
            fps=30,
            max_duration=None,
            description='Discord-friendly 720p (aim for <8MB)',
            crf=28,
        ),
    }

    @classmethod
    def get_preset(cls, name: str) -> VideoFormat:
        """Get a video format preset by name.

        Args:
            name: Preset name (e.g., 'youtube_shorts', 'tiktok')

        Returns:
            VideoFormat configuration

        Raises:
            ValueError: If preset name is not found
        """
        if name not in cls.PRESETS:
            available = ', '.join(cls.PRESETS.keys())
            raise ValueError(f"Unknown preset '{name}'. Available: {available}")
        return cls.PRESETS[name]

    @classmethod
    def list_presets(cls, filter_vertical: Optional[bool] = None) -> List[str]:
        """List available preset names.

        Args:
            filter_vertical: If True, only vertical; if False, only horizontal/square; if None, all

        Returns:
            List of preset names
        """
        if filter_vertical is None:
            return list(cls.PRESETS.keys())
        elif filter_vertical:
            return [k for k, v in cls.PRESETS.items() if v.is_vertical]
        else:
            return [k for k, v in cls.PRESETS.items() if not v.is_vertical]

    @classmethod
    def print_presets(cls):
        """Print formatted list of available presets."""
        print("\nAvailable Video Format Presets:")
        print("=" * 80)

        categories = {
            'Vertical (9:16)': [k for k, v in cls.PRESETS.items() if v.is_vertical],
            'Horizontal (16:9)': [k for k, v in cls.PRESETS.items() if not v.is_vertical and not v.is_square],
            'Square (1:1)': [k for k, v in cls.PRESETS.items() if v.is_square],
        }

        for category, presets in categories.items():
            if presets:
                print(f"\n{category}:")
                for name in presets:
                    fmt = cls.PRESETS[name]
                    duration = f", max {fmt.max_duration}s" if fmt.max_duration else ""
                    print(f"  {name:20} - {fmt.width}x{fmt.height} @ {fmt.fps}fps{duration}")
                    if fmt.description:
                        print(f"  {' ' * 20}   {fmt.description}")


class VideoExporter(ABC):
    """Abstract base class for video exporters.

    Provides common infrastructure for both GL and terminal video export pipelines.
    Subclasses implement the specific rendering logic.
    """

    def __init__(
        self,
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        duration: Optional[float] = None,
        total_frames: Optional[int] = None,
    ):
        """Initialize video exporter.

        Args:
            output_path: Output video file path
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            duration: Video duration in seconds (mutually exclusive with total_frames)
            total_frames: Total number of frames (mutually exclusive with duration)

        Raises:
            ValueError: If neither or both duration and total_frames are specified
        """
        if (duration is None) == (total_frames is None):
            raise ValueError("Must specify exactly one of: duration or total_frames")

        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps

        if duration is not None:
            self.total_frames = int(duration * fps)
            self.duration = duration
        else:
            self.total_frames = total_frames
            self.duration = total_frames / fps

        # Determine output format
        self.is_gif = output_path.lower().endswith('.gif')

        # Initialize shared utilities
        self.encoder = FFmpegEncoder()
        self.progress = None  # Initialized in export()

    @abstractmethod
    def render_frame(self, frame_num: int, temp_dir: str) -> str:
        """Render a single frame and return the saved file path.

        Args:
            frame_num: Frame number (0-indexed)
            temp_dir: Temporary directory for frame storage

        Returns:
            Path to saved frame image file
        """
        pass

    def export(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        crf: int = 23,
        gif_scale: int = 480,
    ) -> bool:
        """Export video by rendering all frames and encoding.

        Args:
            progress_callback: Optional callback(current_frame, total_frames)
            crf: FFmpeg CRF quality (lower = better, 18-28 recommended)
            gif_scale: Max width for GIF output (maintains aspect ratio)

        Returns:
            True if export succeeded, False otherwise
        """
        if not self.encoder.is_available():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        temp_dir = tempfile.mkdtemp(prefix='video_export_')

        try:
            self.progress = ProgressReporter(
                self.total_frames,
                callback=progress_callback,
            )

            print(f"Rendering {self.total_frames} frames at {self.fps} FPS")
            print(f"Resolution: {self.width}x{self.height}")
            print(f"Output: {self.output_path}")
            print()

            # Render all frames
            with self.progress:
                for frame_num in range(self.total_frames):
                    self.render_frame(frame_num, temp_dir)
                    self.progress.update(frame_num + 1)

            print("\nEncoding video...")

            # Encode with ffmpeg
            if self.is_gif:
                success = self.encoder.encode_gif(
                    temp_dir,
                    self.output_path,
                    self.fps,
                    scale=gif_scale,
                )
            else:
                success = self.encoder.encode_video(
                    temp_dir,
                    self.output_path,
                    self.fps,
                    crf=crf,
                )

            if success:
                size = os.path.getsize(self.output_path)
                print(f"\n✓ Video saved: {self.output_path}")
                print(f"  File size: {size / 1024 / 1024:.1f} MB")
                return True
            else:
                print(f"\n✗ Encoding failed")
                return False

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def from_preset(
        cls,
        preset_name: str,
        output_path: str,
        duration: Optional[float] = None,
        **kwargs
    ):
        """Create exporter from a format preset.

        Args:
            preset_name: Name of format preset (e.g., 'youtube_shorts')
            output_path: Output video file path
            duration: Video duration (uses preset max if None and available)
            **kwargs: Additional arguments passed to constructor

        Returns:
            VideoExporter instance configured with preset

        Raises:
            ValueError: If preset is not found
        """
        preset = PresetManager.get_preset(preset_name)

        # Use preset's max duration if duration not specified
        if duration is None and preset.max_duration is not None:
            duration = preset.max_duration

        if duration is None:
            raise ValueError(f"Must specify duration for preset '{preset_name}'")

        return cls(
            output_path=output_path,
            width=preset.width,
            height=preset.height,
            fps=preset.fps,
            duration=duration,
            **kwargs
        )
