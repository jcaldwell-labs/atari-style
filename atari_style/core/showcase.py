#!/usr/bin/env python3
"""Demo showcase generator for creating playlist videos.

Concatenates multiple demo exports into a single showcase video,
optionally with title cards between demos.

Usage:
    python -m atari_style.core.showcase create \\
        --input joystick.mp4 starfield.mp4 \\
        --output showcase.mp4

    python -m atari_style.core.showcase create \\
        --input joystick.mp4 starfield.mp4 \\
        --titles "Joystick Test" "Starfield Demo" \\
        --output showcase.mp4

    python -m atari_style.core.showcase create --manifest showcase.json
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .headless_renderer import (
    HeadlessRenderer,
    ANSI_COLORS,
    DEFAULT_BG_COLOR,
)


@dataclass
class ShowcaseEntry:
    """A single entry in the showcase playlist."""
    video_path: str
    title: Optional[str] = None
    title_duration: float = 2.0  # seconds


@dataclass
class ShowcaseManifest:
    """Manifest for building a showcase video."""
    entries: List[ShowcaseEntry] = field(default_factory=list)
    output_path: str = "showcase.mp4"
    title_duration: float = 2.0
    title_style: str = "terminal"  # terminal, minimal
    fps: int = 30
    width: int = 800
    height: int = 480

    @classmethod
    def from_json(cls, path: str) -> 'ShowcaseManifest':
        """Load manifest from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        entries = []
        for entry_data in data.get('entries', []):
            if isinstance(entry_data, str):
                entries.append(ShowcaseEntry(video_path=entry_data))
            else:
                entries.append(ShowcaseEntry(
                    video_path=entry_data['video'],
                    title=entry_data.get('title'),
                    title_duration=entry_data.get('title_duration', data.get('title_duration', 2.0)),
                ))

        return cls(
            entries=entries,
            output_path=data.get('output', 'showcase.mp4'),
            title_duration=data.get('title_duration', 2.0),
            title_style=data.get('title_style', 'terminal'),
            fps=data.get('fps', 30),
            width=data.get('width', 800),
            height=data.get('height', 480),
        )

    def to_json(self, path: str) -> None:
        """Save manifest to JSON file."""
        data = {
            'output': self.output_path,
            'title_duration': self.title_duration,
            'title_style': self.title_style,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'entries': [
                {
                    'video': e.video_path,
                    'title': e.title,
                    'title_duration': e.title_duration,
                } if e.title else e.video_path
                for e in self.entries
            ],
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


class TitleCardGenerator:
    """Generates title card videos in terminal style."""

    def __init__(
        self,
        width: int = 800,
        height: int = 480,
        fps: int = 30,
        style: str = "terminal",
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.style = style

        # Terminal grid dimensions
        self.char_width = 10
        self.char_height = 20
        self.grid_width = width // self.char_width
        self.grid_height = height // self.char_height

    def _create_terminal_title(self, title: str) -> Image.Image:
        """Create a title card image in terminal style."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow required for title card generation")

        # Create headless renderer for consistent terminal look
        renderer = HeadlessRenderer(
            width=self.grid_width,
            height=self.grid_height,
            char_width=self.char_width,
            char_height=self.char_height,
        )

        # Draw decorative border
        renderer.draw_border(0, 0, self.grid_width, self.grid_height, 'cyan')

        # Center the title
        title_x = (self.grid_width - len(title)) // 2
        title_y = self.grid_height // 2

        # Draw title with glow effect (draw behind in darker color)
        if title_x > 0:
            renderer.draw_text(title_x, title_y, title, 'bright_cyan')

        # Add decorative lines above and below
        line_char = '─'
        line_width = min(len(title) + 8, self.grid_width - 4)
        line_x = (self.grid_width - line_width) // 2

        line_above = line_char * line_width
        line_below = line_char * line_width

        renderer.draw_text(line_x, title_y - 2, line_above, 'cyan')
        renderer.draw_text(line_x, title_y + 2, line_below, 'cyan')

        # Add corner decorations
        if line_x > 0 and title_y > 2:
            renderer.draw_text(line_x - 1, title_y - 2, '╭', 'cyan')
            renderer.draw_text(line_x + line_width, title_y - 2, '╮', 'cyan')
            renderer.draw_text(line_x - 1, title_y + 2, '╰', 'cyan')
            renderer.draw_text(line_x + line_width, title_y + 2, '╯', 'cyan')

        return renderer.to_image()

    def _create_minimal_title(self, title: str) -> Image.Image:
        """Create a minimal title card."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow required for title card generation")

        img = Image.new('RGB', (self.width, self.height), DEFAULT_BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Try to use a monospace font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        draw.text((x, y), title, fill=ANSI_COLORS['bright_cyan'], font=font)

        return img

    def generate(self, title: str, duration: float, output_path: str) -> None:
        """Generate a title card video.

        Args:
            title: Text to display
            duration: Duration in seconds
            output_path: Output video file path
        """
        if self.style == "terminal":
            img = self._create_terminal_title(title)
        else:
            img = self._create_minimal_title(title)

        # Save as temporary image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_img = f.name

        try:
            img.save(temp_img)

            # Use ffmpeg to create video from static image
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', temp_img,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', str(self.fps),
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        finally:
            os.unlink(temp_img)


class ShowcaseGenerator:
    """Generates showcase videos by concatenating demos."""

    def __init__(self, manifest: ShowcaseManifest):
        self.manifest = manifest
        self.title_generator = TitleCardGenerator(
            width=manifest.width,
            height=manifest.height,
            fps=manifest.fps,
            style=manifest.title_style,
        )

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        return shutil.which('ffmpeg') is not None

    def _get_video_info(self, path: str) -> Tuple[int, int, int]:
        """Get video dimensions and fps using ffprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate',
            '-of', 'json',
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed for {path}: {result.stderr}")

        data = json.loads(result.stdout)
        stream = data['streams'][0]
        width = stream['width']
        height = stream['height']

        # Parse frame rate (can be "30/1" or "30000/1001")
        fps_str = stream['r_frame_rate']
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = round(int(num) / int(den))
        else:
            fps = round(float(fps_str))

        return width, height, fps

    def _normalize_video(
        self,
        input_path: str,
        output_path: str,
        target_width: int,
        target_height: int,
        target_fps: int,
    ) -> None:
        """Normalize video to target resolution and fps."""
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,'
                   f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2',
            '-r', str(target_fps),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-an',  # Remove audio for now
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg normalization failed: {result.stderr}")

    def generate(self, progress_callback=None) -> str:
        """Generate the showcase video.

        Args:
            progress_callback: Optional callback(step, total, message)

        Returns:
            Path to output video
        """
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        if not self.manifest.entries:
            raise ValueError("No entries in manifest")

        # Validate input files exist
        for entry in self.manifest.entries:
            if not os.path.exists(entry.video_path):
                raise FileNotFoundError(f"Video not found: {entry.video_path}")

        # Get target dimensions from first video or manifest
        if self.manifest.width and self.manifest.height:
            target_width = self.manifest.width
            target_height = self.manifest.height
        else:
            target_width, target_height, _ = self._get_video_info(
                self.manifest.entries[0].video_path
            )
        target_fps = self.manifest.fps

        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            segments = []
            # Count actual steps: one per entry (normalize) + one per entry with title
            total_steps = len(self.manifest.entries) + sum(1 for e in self.manifest.entries if e.title)
            step = 0

            for i, entry in enumerate(self.manifest.entries):
                # Generate title card if title provided
                if entry.title:
                    step += 1
                    if progress_callback:
                        progress_callback(step, total_steps, f"Creating title: {entry.title}")

                    title_path = os.path.join(temp_dir, f"title_{i:03d}.mp4")
                    self.title_generator.generate(
                        entry.title,
                        entry.title_duration,
                        title_path,
                    )
                    segments.append(title_path)

                # Normalize video segment
                step += 1
                if progress_callback:
                    progress_callback(step, total_steps, f"Processing: {entry.video_path}")

                normalized_path = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                self._normalize_video(
                    entry.video_path,
                    normalized_path,
                    target_width,
                    target_height,
                    target_fps,
                )
                segments.append(normalized_path)

            # Create concat file
            concat_file = os.path.join(temp_dir, "concat.txt")
            with open(concat_file, 'w') as f:
                for seg in segments:
                    # Escape special characters in path
                    escaped = seg.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            # Concatenate all segments
            if progress_callback:
                progress_callback(total_steps, total_steps, "Concatenating segments...")

            output_path = self.manifest.output_path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")

        return output_path


def create_showcase(
    input_videos: List[str],
    output_path: str,
    titles: Optional[List[str]] = None,
    title_duration: float = 2.0,
    title_style: str = "terminal",
    fps: int = 30,
    width: Optional[int] = None,
    height: Optional[int] = None,
    progress_callback=None,
) -> str:
    """Convenience function to create a showcase video.

    Args:
        input_videos: List of video file paths
        output_path: Output video path
        titles: Optional list of titles (must match input_videos length)
        title_duration: Duration for each title card
        title_style: Style for title cards ("terminal" or "minimal")
        fps: Output frame rate
        width: Output width (None = auto from first video)
        height: Output height (None = auto from first video)
        progress_callback: Optional callback(step, total, message)

    Returns:
        Path to output video
    """
    if titles and len(titles) != len(input_videos):
        raise ValueError("Number of titles must match number of input videos")

    entries = []
    for i, video in enumerate(input_videos):
        title = titles[i] if titles else None
        entries.append(ShowcaseEntry(
            video_path=video,
            title=title,
            title_duration=title_duration,
        ))

    # Auto-detect dimensions from first video if not specified
    if width is None or height is None:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            input_videos[0],
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            stream = data['streams'][0]
            width = width or stream['width']
            height = height or stream['height']
        else:
            width = width or 800
            height = height or 480

    manifest = ShowcaseManifest(
        entries=entries,
        output_path=output_path,
        title_duration=title_duration,
        title_style=title_style,
        fps=fps,
        width=width,
        height=height,
    )

    generator = ShowcaseGenerator(manifest)
    return generator.generate(progress_callback)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create showcase videos from multiple demo exports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --input demo1.mp4 demo2.mp4 -o showcase.mp4
  %(prog)s create --input demo1.mp4 demo2.mp4 --titles "Demo 1" "Demo 2" -o showcase.mp4
  %(prog)s create --manifest showcase.json
  %(prog)s init --output showcase.json demo1.mp4 demo2.mp4
""",
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create command
    create_parser = subparsers.add_parser('create', help='Create showcase video')
    create_parser.add_argument('--input', '-i', nargs='+', help='Input video files')
    create_parser.add_argument('--titles', '-t', nargs='+', help='Title cards for each video')
    create_parser.add_argument('--manifest', '-m', help='Manifest JSON file')
    create_parser.add_argument('--output', '-o', help='Output video file')
    create_parser.add_argument('--title-duration', type=float, default=2.0,
                               help='Title card duration in seconds (default: 2.0)')
    create_parser.add_argument('--title-style', choices=['terminal', 'minimal'],
                               default='terminal', help='Title card style (default: terminal)')
    create_parser.add_argument('--fps', type=int, default=30,
                               help='Output frame rate (default: 30)')
    create_parser.add_argument('--width', type=int, help='Output width')
    create_parser.add_argument('--height', type=int, help='Output height')

    # Init command (create manifest template)
    init_parser = subparsers.add_parser('init', help='Create manifest template')
    init_parser.add_argument('videos', nargs='+', help='Video files to include')
    init_parser.add_argument('--output', '-o', default='showcase.json',
                             help='Output manifest file (default: showcase.json)')

    args = parser.parse_args()

    if args.command == 'init':
        # Create manifest template
        entries = [ShowcaseEntry(video_path=v) for v in args.videos]
        manifest = ShowcaseManifest(entries=entries)
        manifest.to_json(args.output)
        print(f"Created manifest: {args.output}")
        print("Edit the file to add titles and customize settings.")
        return

    if args.command == 'create':
        if args.manifest:
            # Load from manifest
            manifest = ShowcaseManifest.from_json(args.manifest)
            if args.output:
                manifest.output_path = args.output
        elif args.input:
            # Build from CLI args
            if not args.output:
                parser.error("--output required when using --input")

            entries = []
            for i, video in enumerate(args.input):
                title = args.titles[i] if args.titles and i < len(args.titles) else None
                entries.append(ShowcaseEntry(
                    video_path=video,
                    title=title,
                    title_duration=args.title_duration,
                ))

            manifest = ShowcaseManifest(
                entries=entries,
                output_path=args.output,
                title_duration=args.title_duration,
                title_style=args.title_style,
                fps=args.fps,
                width=args.width or 800,
                height=args.height or 480,
            )
        else:
            parser.error("Either --manifest or --input is required")

        def progress(step, total, msg):
            print(f"[{step}/{total}] {msg}")

        try:
            generator = ShowcaseGenerator(manifest)
            output = generator.generate(progress_callback=progress)
            print(f"\nShowcase created: {output}")
        except Exception as e:
            print(f"Error: {e}")
            return 1

    return 0


if __name__ == '__main__':
    exit(main() or 0)
