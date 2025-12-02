"""Video storyboard system for keyframe planning and review (Issue #47).

Provides a workflow for planning animation keyframes, previewing them before
rendering, and generating full videos with parameter interpolation.

Usage:
    from atari_style.core.gl.storyboard import Storyboard, StoryboardRenderer

    # Load a storyboard
    storyboard = Storyboard.from_file('storyboards/plasma-demo.json')

    # Preview keyframes
    renderer = StoryboardRenderer()
    renderer.preview_keyframes(storyboard, 'keyframes/')

    # Generate contact sheet
    renderer.create_contact_sheet(storyboard, 'contact-sheet.png')

    # Render full video
    renderer.render_video(storyboard, 'output.mp4')

CLI:
    python -m atari_style.core.gl.storyboard preview plasma-demo.json -o keyframes/
    python -m atari_style.core.gl.storyboard grid plasma-demo.json -o contact.png
    python -m atari_style.core.gl.storyboard render plasma-demo.json -o output.mp4
    python -m atari_style.core.gl.storyboard validate plasma-demo.json
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

from .composites import CompositeManager, COMPOSITES, CompositeConfig
from .video_export import VideoExporter, VIDEO_FORMATS, VideoFormat


# Schema version for forward compatibility
SCHEMA_VERSION = "1.0"


@dataclass
class Keyframe:
    """A single keyframe in a storyboard."""
    id: str
    time: float  # Time in seconds
    composite: Optional[str] = None  # Inherits from storyboard if None
    params: Optional[Tuple[float, float, float, float]] = None  # Inherits if None
    color_mode: Optional[int] = None  # Inherits if None
    note: str = ""  # Human-readable description for review

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = {"id": self.id, "time": self.time}
        if self.composite:
            d["composite"] = self.composite
        if self.params:
            d["params"] = list(self.params)
        if self.color_mode is not None:
            d["color_mode"] = self.color_mode
        if self.note:
            d["note"] = self.note
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'Keyframe':
        """Create from dictionary."""
        params = tuple(data["params"]) if "params" in data else None
        return cls(
            id=data["id"],
            time=data["time"],
            composite=data.get("composite"),
            params=params,
            color_mode=data.get("color_mode"),
            note=data.get("note", "")
        )


@dataclass
class Storyboard:
    """A storyboard defining an animation sequence."""
    title: str
    composite: str  # Default composite for all keyframes
    keyframes: List[Keyframe]
    format: str = "youtube_shorts"  # Video format preset name
    fps: int = 30
    description: str = ""
    transitions: str = "linear"  # linear, ease_in_out, step
    version: str = SCHEMA_VERSION
    default_params: Optional[Tuple[float, float, float, float]] = None
    default_color_mode: int = 0

    def __post_init__(self):
        """Sort keyframes by time after initialization."""
        self.keyframes = sorted(self.keyframes, key=lambda k: k.time)

    @property
    def duration(self) -> float:
        """Total duration based on last keyframe time."""
        if not self.keyframes:
            return 0.0
        return self.keyframes[-1].time

    @property
    def video_format(self) -> VideoFormat:
        """Get the VideoFormat object for this storyboard."""
        return VIDEO_FORMATS.get(self.format, VIDEO_FORMATS["youtube_shorts"])

    def get_params_at_time(self, time: float) -> Tuple[float, float, float, float]:
        """Get interpolated parameters at a specific time.

        Args:
            time: Time in seconds

        Returns:
            Interpolated parameter tuple
        """
        if not self.keyframes:
            return self.default_params or COMPOSITES[self.composite].default_params

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for kf in self.keyframes:
            if kf.time <= time:
                prev_kf = kf
            elif next_kf is None:
                next_kf = kf
                break

        # Before first keyframe
        if prev_kf is None:
            kf = self.keyframes[0]
            return kf.params or self.default_params or COMPOSITES[self.composite].default_params

        # After last keyframe or exactly on a keyframe
        if next_kf is None or prev_kf.time == time:
            return prev_kf.params or self.default_params or COMPOSITES[self.composite].default_params

        # Interpolate between keyframes
        prev_params = prev_kf.params or self.default_params or COMPOSITES[self.composite].default_params
        next_params = next_kf.params or self.default_params or COMPOSITES[self.composite].default_params

        # Calculate interpolation factor
        t = (time - prev_kf.time) / (next_kf.time - prev_kf.time)

        # Apply transition easing
        t = self._apply_easing(t)

        # Linear interpolation for each parameter
        return tuple(
            prev_params[i] + t * (next_params[i] - prev_params[i])
            for i in range(4)
        )

    def _apply_easing(self, t: float) -> float:
        """Apply easing function to interpolation factor.

        Args:
            t: Linear interpolation factor (0-1)

        Returns:
            Eased interpolation factor
        """
        if self.transitions == "step":
            return 0.0 if t < 1.0 else 1.0
        elif self.transitions == "ease_in_out":
            # Smooth step: 3t^2 - 2t^3
            return t * t * (3 - 2 * t)
        else:  # linear
            return t

    def get_color_mode_at_time(self, time: float) -> int:
        """Get color mode at a specific time (uses nearest keyframe)."""
        if not self.keyframes:
            return self.default_color_mode

        # Find nearest keyframe
        nearest = min(self.keyframes, key=lambda k: abs(k.time - time))
        return nearest.color_mode if nearest.color_mode is not None else self.default_color_mode

    def get_composite_at_time(self, time: float) -> str:
        """Get composite name at a specific time."""
        if not self.keyframes:
            return self.composite

        # Find active keyframe (last keyframe at or before time)
        active = None
        for kf in self.keyframes:
            if kf.time <= time:
                active = kf
            else:
                break

        if active and active.composite:
            return active.composite
        return self.composite

    def validate(self) -> List[str]:
        """Validate the storyboard and return list of errors."""
        errors = []

        # Check composite exists
        if self.composite not in COMPOSITES:
            errors.append(f"Unknown composite: {self.composite}")

        # Check format exists
        if self.format not in VIDEO_FORMATS:
            errors.append(f"Unknown format: {self.format}")

        # Check keyframes
        if not self.keyframes:
            errors.append("No keyframes defined")

        for kf in self.keyframes:
            if kf.composite and kf.composite not in COMPOSITES:
                errors.append(f"Keyframe '{kf.id}': Unknown composite '{kf.composite}'")
            if kf.params and len(kf.params) != 4:
                errors.append(f"Keyframe '{kf.id}': params must have 4 values")
            if kf.time < 0:
                errors.append(f"Keyframe '{kf.id}': negative time not allowed")

        # Check duration vs format limit
        fmt = self.video_format
        if fmt.max_duration and self.duration > fmt.max_duration:
            errors.append(
                f"Duration {self.duration}s exceeds {fmt.name} limit of {fmt.max_duration}s"
            )

        # Check transitions
        if self.transitions not in ("linear", "ease_in_out", "step"):
            errors.append(f"Unknown transition type: {self.transitions}")

        return errors

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = {
            "version": self.version,
            "title": self.title,
            "composite": self.composite,
            "format": self.format,
            "fps": self.fps,
            "transitions": self.transitions,
            "keyframes": [kf.to_dict() for kf in self.keyframes],
        }
        if self.description:
            d["description"] = self.description
        if self.default_params:
            d["default_params"] = list(self.default_params)
        if self.default_color_mode != 0:
            d["default_color_mode"] = self.default_color_mode
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'Storyboard':
        """Create from dictionary."""
        keyframes = [Keyframe.from_dict(kf) for kf in data.get("keyframes", [])]
        default_params = tuple(data["default_params"]) if "default_params" in data else None

        return cls(
            title=data["title"],
            composite=data["composite"],
            keyframes=keyframes,
            format=data.get("format", "youtube_shorts"),
            fps=data.get("fps", 30),
            description=data.get("description", ""),
            transitions=data.get("transitions", "linear"),
            version=data.get("version", SCHEMA_VERSION),
            default_params=default_params,
            default_color_mode=data.get("default_color_mode", 0),
        )

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'Storyboard':
        """Load storyboard from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, path: Union[str, Path]) -> None:
        """Save storyboard to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)


class StoryboardRenderer:
    """Renderer for storyboard keyframes and videos."""

    def __init__(self):
        """Initialize the renderer."""
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")
        self._manager: Optional[CompositeManager] = None

    def _get_manager(self, width: int, height: int) -> CompositeManager:
        """Get or create a CompositeManager with specified dimensions."""
        if self._manager is None or self._manager.width != width or self._manager.height != height:
            self._manager = CompositeManager(width, height)
        return self._manager

    def render_keyframe(self, storyboard: Storyboard, keyframe: Keyframe,
                        width: Optional[int] = None,
                        height: Optional[int] = None) -> 'Image.Image':
        """Render a single keyframe.

        Args:
            storyboard: Parent storyboard
            keyframe: Keyframe to render
            width: Override width (uses format default if None)
            height: Override height (uses format default if None)

        Returns:
            PIL Image of the rendered keyframe
        """
        fmt = storyboard.video_format
        w = width or fmt.width
        h = height or fmt.height

        composite = keyframe.composite or storyboard.composite
        params = keyframe.params or storyboard.default_params
        color_mode = keyframe.color_mode if keyframe.color_mode is not None else storyboard.default_color_mode

        manager = self._get_manager(w, h)
        return manager.render_frame(composite, keyframe.time, params, color_mode, w, h)

    def preview_keyframes(self, storyboard: Storyboard, output_dir: Union[str, Path],
                          width: Optional[int] = None,
                          height: Optional[int] = None) -> List[str]:
        """Export all keyframes as individual PNG files.

        Args:
            storyboard: Storyboard to preview
            output_dir: Directory for output PNGs
            width: Override width
            height: Override height

        Returns:
            List of output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, kf in enumerate(storyboard.keyframes):
            img = self.render_keyframe(storyboard, kf, width, height)

            filename = f"{i:02d}_{kf.id}.png"
            path = output_dir / filename
            img.save(path, 'PNG')
            paths.append(str(path))

            print(f"  [{i+1}/{len(storyboard.keyframes)}] {kf.id} @ {kf.time:.1f}s -> {filename}")

        return paths

    def create_contact_sheet(self, storyboard: Storyboard, output_path: Union[str, Path],
                             thumb_width: int = 320, thumb_height: int = 180,
                             cols: int = 3, padding: int = 10,
                             show_notes: bool = True) -> str:
        """Generate a contact sheet grid of all keyframes.

        Args:
            storyboard: Storyboard to render
            output_path: Output PNG path
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height
            cols: Number of columns in grid
            padding: Padding between thumbnails
            show_notes: Show keyframe notes/captions

        Returns:
            Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        n = len(storyboard.keyframes)
        rows = (n + cols - 1) // cols

        # Calculate contact sheet dimensions
        text_height = 40 if show_notes else 20
        cell_width = thumb_width + padding
        cell_height = thumb_height + text_height + padding
        sheet_width = cols * cell_width + padding
        sheet_height = rows * cell_height + padding + 60  # Header space

        # Create sheet
        sheet = Image.new('RGB', (sheet_width, sheet_height), (30, 30, 46))
        draw = ImageDraw.Draw(sheet)

        # Try to load a font
        try:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "C:\\Windows\\Fonts\\consola.ttf",
                "/System/Library/Fonts/Monaco.dfont",
            ]
            font = None
            small_font = None
            for fp in font_paths:
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, 14)
                    small_font = ImageFont.truetype(fp, 11)
                    break
            if font is None:
                font = ImageFont.load_default()
                small_font = font
        except Exception:
            font = ImageFont.load_default()
            small_font = font

        # Draw header
        draw.text((padding, padding), storyboard.title, fill=(255, 255, 255), font=font)
        fmt = storyboard.video_format
        info = f"{fmt.name} | {fmt.width}x{fmt.height} | {storyboard.fps} FPS | {storyboard.duration:.1f}s"
        draw.text((padding, padding + 20), info, fill=(150, 150, 150), font=small_font)

        # Render keyframes
        for i, kf in enumerate(storyboard.keyframes):
            row = i // cols
            col = i % cols

            x = padding + col * cell_width
            y = 60 + padding + row * cell_height

            # Render thumbnail
            img = self.render_keyframe(storyboard, kf, thumb_width, thumb_height)
            img = img.convert('RGB')
            sheet.paste(img, (x, y))

            # Draw border
            draw.rectangle(
                [x - 1, y - 1, x + thumb_width, y + thumb_height],
                outline=(100, 100, 100)
            )

            # Draw timestamp
            time_str = f"{kf.time:.1f}s"
            draw.text((x + 5, y + thumb_height + 2), f"{kf.id}", fill=(255, 255, 255), font=small_font)
            draw.text((x + thumb_width - 40, y + thumb_height + 2), time_str, fill=(150, 150, 150), font=small_font)

            # Draw note if enabled
            if show_notes and kf.note:
                note = kf.note[:40] + "..." if len(kf.note) > 40 else kf.note
                draw.text((x + 5, y + thumb_height + 18), note, fill=(100, 150, 100), font=small_font)

        sheet.save(output_path, 'PNG')
        print(f"Contact sheet saved to: {output_path}")
        return str(output_path)

    def render_video(self, storyboard: Storyboard, output_path: Union[str, Path],
                     progress_callback=None) -> bool:
        """Render the full video with parameter interpolation.

        Args:
            storyboard: Storyboard to render
            output_path: Output video path
            progress_callback: Optional callback(current_frame, total_frames)

        Returns:
            True if successful
        """
        fmt = storyboard.video_format
        exporter = VideoExporter(fmt.width, fmt.height, storyboard.fps)

        # We'll use a custom render loop that respects keyframe interpolation
        total_frames = int(storyboard.duration * storyboard.fps)

        print(f"Storyboard: {storyboard.title}")
        print(f"Format: {fmt.name} ({fmt.width}x{fmt.height})")
        print(f"Duration: {storyboard.duration}s ({total_frames} frames)")
        print(f"Keyframes: {len(storyboard.keyframes)}")
        print(f"Transitions: {storyboard.transitions}")
        print()

        import tempfile
        import subprocess
        import shutil

        temp_dir = tempfile.mkdtemp(prefix='storyboard_')

        try:
            manager = self._get_manager(fmt.width, fmt.height)

            for frame_num in range(total_frames):
                time_val = frame_num / storyboard.fps

                # Get interpolated values at this time
                composite = storyboard.get_composite_at_time(time_val)
                params = storyboard.get_params_at_time(time_val)
                color_mode = storyboard.get_color_mode_at_time(time_val)

                # Render frame
                img = manager.render_frame(composite, time_val, params, color_mode,
                                           fmt.width, fmt.height)

                # Save frame
                frame_path = os.path.join(temp_dir, f"frame_{frame_num:06d}.png")
                img.save(frame_path, 'PNG')

                if progress_callback:
                    progress_callback(frame_num + 1, total_frames)
                elif (frame_num + 1) % 30 == 0:
                    percent = (frame_num + 1) / total_frames * 100
                    print(f"  Frame {frame_num + 1}/{total_frames} ({percent:.0f}%)")

            print(f"\nAll frames rendered. Encoding video...")

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Encode with ffmpeg
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(storyboard.fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18',
                '-preset', 'medium',
                str(output_path)
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
            shutil.rmtree(temp_dir, ignore_errors=True)


def validate_storyboard(path: Union[str, Path]) -> List[str]:
    """Validate a storyboard file and return errors.

    Args:
        path: Path to storyboard JSON

    Returns:
        List of error messages (empty if valid)
    """
    try:
        storyboard = Storyboard.from_file(path)
        return storyboard.validate()
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except KeyError as e:
        return [f"Missing required field: {e}"]
    except Exception as e:
        return [f"Error loading storyboard: {e}"]


def main():
    """Command-line interface for storyboard operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Video storyboard system for keyframe planning and review',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  validate  Check storyboard for errors
  preview   Export keyframes as individual PNGs
  grid      Generate contact sheet of all keyframes
  render    Render full video with interpolation

Examples:
  %(prog)s validate storyboards/plasma-demo.json
  %(prog)s preview storyboards/plasma-demo.json -o keyframes/
  %(prog)s grid storyboards/plasma-demo.json -o contact.png
  %(prog)s render storyboards/plasma-demo.json -o output.mp4
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate storyboard')
    validate_parser.add_argument('storyboard', help='Storyboard JSON file')

    # preview command
    preview_parser = subparsers.add_parser('preview', help='Export keyframe PNGs')
    preview_parser.add_argument('storyboard', help='Storyboard JSON file')
    preview_parser.add_argument('-o', '--output', default='keyframes/',
                                help='Output directory (default: keyframes/)')
    preview_parser.add_argument('--width', type=int, help='Override width')
    preview_parser.add_argument('--height', type=int, help='Override height')

    # grid command
    grid_parser = subparsers.add_parser('grid', help='Generate contact sheet')
    grid_parser.add_argument('storyboard', help='Storyboard JSON file')
    grid_parser.add_argument('-o', '--output', default='contact-sheet.png',
                             help='Output PNG path (default: contact-sheet.png)')
    grid_parser.add_argument('--cols', type=int, default=3, help='Grid columns (default: 3)')
    grid_parser.add_argument('--thumb-width', type=int, default=320,
                             help='Thumbnail width (default: 320)')
    grid_parser.add_argument('--thumb-height', type=int, default=180,
                             help='Thumbnail height (default: 180)')
    grid_parser.add_argument('--no-notes', action='store_true',
                             help='Hide keyframe notes')

    # render command
    render_parser = subparsers.add_parser('render', help='Render full video')
    render_parser.add_argument('storyboard', help='Storyboard JSON file')
    render_parser.add_argument('-o', '--output', help='Output video path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'validate':
        errors = validate_storyboard(args.storyboard)
        if errors:
            print(f"Validation FAILED for {args.storyboard}:")
            for err in errors:
                print(f"  - {err}")
            return 1
        else:
            storyboard = Storyboard.from_file(args.storyboard)
            print(f"Validation PASSED for {args.storyboard}")
            print(f"  Title: {storyboard.title}")
            print(f"  Composite: {storyboard.composite}")
            print(f"  Format: {storyboard.format}")
            print(f"  Duration: {storyboard.duration}s")
            print(f"  Keyframes: {len(storyboard.keyframes)}")
            return 0

    elif args.command == 'preview':
        storyboard = Storyboard.from_file(args.storyboard)
        errors = storyboard.validate()
        if errors:
            print("Storyboard has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1

        print(f"Previewing {len(storyboard.keyframes)} keyframes from {storyboard.title}")
        renderer = StoryboardRenderer()
        paths = renderer.preview_keyframes(storyboard, args.output, args.width, args.height)
        print(f"\nExported {len(paths)} keyframes to {args.output}")
        return 0

    elif args.command == 'grid':
        storyboard = Storyboard.from_file(args.storyboard)
        errors = storyboard.validate()
        if errors:
            print("Storyboard has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1

        print(f"Generating contact sheet for {storyboard.title}")
        renderer = StoryboardRenderer()
        renderer.create_contact_sheet(
            storyboard, args.output,
            thumb_width=args.thumb_width,
            thumb_height=args.thumb_height,
            cols=args.cols,
            show_notes=not args.no_notes
        )
        return 0

    elif args.command == 'render':
        storyboard = Storyboard.from_file(args.storyboard)
        errors = storyboard.validate()
        if errors:
            print("Storyboard has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1

        output = args.output or f"{storyboard.title.lower().replace(' ', '_')}.mp4"
        renderer = StoryboardRenderer()
        success = renderer.render_video(storyboard, output)
        return 0 if success else 1


if __name__ == '__main__':
    exit(main() or 0)
