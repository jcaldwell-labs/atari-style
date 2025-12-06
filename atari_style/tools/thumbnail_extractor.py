#!/usr/bin/env python3
"""Thumbnail Frame Extractor - Extract key frames for YouTube thumbnails.

Extract key frames suitable for YouTube thumbnails from video scripts.
Supports multiple frame selection strategies and outputs PNG files.

Usage:
    python -m atari_style.tools.thumbnail_extractor script.json -o thumbnails/
    python -m atari_style.tools.thumbnail_extractor script.json --count 5 -o thumbnails/
    cat script.json | python -m atari_style.tools.thumbnail_extractor - -o thumbnails/

Examples:
    # Extract 3 evenly spaced frames (default)
    python -m atari_style.tools.thumbnail_extractor scripts/videos/lissajous-intro.json -o out/

    # Extract 5 frames
    python -m atari_style.tools.thumbnail_extractor scripts/videos/lissajous-intro.json --count 5 -o out/

    # Extract only title card frames
    python -m atari_style.tools.thumbnail_extractor scripts/videos/lissajous-intro.json --strategy title -o out/

    # Read from stdin (pipeline support)
    cat script.json | python -m atari_style.tools.thumbnail_extractor - -o out/
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..core.video_script import (
    VideoScript,
    TitleSegment,
    SegmentType,
)

# YouTube recommended thumbnail resolution
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


@dataclass
class FrameInfo:
    """Information about a selected frame."""
    frame_number: int
    timestamp: float
    segment_index: int
    segment_type: str
    description: str


def load_script(script_arg: str) -> VideoScript:
    """Load a video script from file or stdin.

    Args:
        script_arg: Path to script file, or '-' for stdin

    Returns:
        VideoScript object

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if script_arg == '-':
        data = json.load(sys.stdin)
        return VideoScript.from_dict(data)
    else:
        script_path = Path(script_arg)
        if not script_path.exists():
            raise FileNotFoundError(script_path)
        return VideoScript.from_file(script_path)


def get_segment_start_times(script: VideoScript) -> List[float]:
    """Calculate start time for each segment.

    Args:
        script: VideoScript to process

    Returns:
        List of start times in seconds for each segment
    """
    start_times = []
    current_time = 0.0
    for segment in script.segments:
        start_times.append(current_time)
        current_time += segment.duration
    return start_times


def select_evenly_spaced_frames(
    script: VideoScript,
    count: int
) -> List[FrameInfo]:
    """Select evenly spaced frames throughout the video.

    Args:
        script: VideoScript to process
        count: Number of frames to select

    Returns:
        List of FrameInfo objects for selected frames
    """
    if not script.segments:
        return []

    total_duration = script.total_duration
    fps = script.format.fps
    total_frames = int(total_duration * fps)

    if count <= 0 or total_frames == 0:
        return []

    # Calculate frame interval
    if count == 1:
        frame_numbers = [total_frames // 2]
    else:
        # Spread frames evenly, avoiding first and last frame
        interval = total_frames / (count + 1)
        frame_numbers = [int(interval * (i + 1)) for i in range(count)]

    # Get segment start times for mapping
    start_times = get_segment_start_times(script)

    frames = []
    for frame_num in frame_numbers:
        timestamp = frame_num / fps
        # Find which segment this frame belongs to
        seg_index = 0
        for i, start in enumerate(start_times):
            if i + 1 < len(start_times):
                if start <= timestamp < start_times[i + 1]:
                    seg_index = i
                    break
            else:
                seg_index = i

        segment = script.segments[seg_index]
        seg_type = segment.get_type().value

        # Generate description
        if isinstance(segment, TitleSegment):
            desc = f"Title: {segment.text}"
        else:
            desc = f"Frame at {timestamp:.2f}s"

        frames.append(FrameInfo(
            frame_number=frame_num,
            timestamp=timestamp,
            segment_index=seg_index,
            segment_type=seg_type,
            description=desc
        ))

    return frames


def select_title_card_frames(script: VideoScript) -> List[FrameInfo]:
    """Select frames from title card segments.

    Args:
        script: VideoScript to process

    Returns:
        List of FrameInfo objects for title card frames
    """
    if not script.segments:
        return []

    fps = script.format.fps
    start_times = get_segment_start_times(script)

    frames = []
    for i, segment in enumerate(script.segments):
        if segment.get_type() == SegmentType.TITLE:
            # Select frame at middle of title segment
            seg_start = start_times[i]
            seg_mid = seg_start + (segment.duration / 2)
            frame_num = int(seg_mid * fps)

            title_seg = segment
            if isinstance(title_seg, TitleSegment):
                desc = f"Title: {title_seg.text}"
            else:
                desc = f"Title at {seg_mid:.2f}s"

            frames.append(FrameInfo(
                frame_number=frame_num,
                timestamp=seg_mid,
                segment_index=i,
                segment_type='title',
                description=desc
            ))

    return frames


def select_frames(
    script: VideoScript,
    strategy: str,
    count: int
) -> List[FrameInfo]:
    """Select frames based on the specified strategy.

    Args:
        script: VideoScript to process
        strategy: Selection strategy ('evenly_spaced' or 'title')
        count: Number of frames (for evenly_spaced strategy)

    Returns:
        List of FrameInfo objects for selected frames
    """
    if strategy == 'title':
        return select_title_card_frames(script)
    else:
        return select_evenly_spaced_frames(script, count)


def generate_placeholder_frame(
    frame_info: FrameInfo,
    script: VideoScript,
    output_path: Path
) -> bool:
    """Generate a placeholder PNG frame.

    Since actual video rendering is not yet implemented, this creates
    a placeholder image with frame information.

    Args:
        frame_info: Information about the frame to generate
        script: VideoScript for context
        output_path: Path to save the PNG file

    Returns:
        True if frame was generated successfully
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Warning: Pillow not available, creating minimal placeholder",
              file=sys.stderr)
        # Create minimal 1x1 pixel image
        with open(output_path, 'wb') as f:
            # PNG header for a 1x1 black pixel
            f.write(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
                b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
                b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
            )
        return True

    # Create image with dark background
    img = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Try to use a reasonable font with cross-platform fallbacks
    font_paths = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    font_large = None
    font_medium = None
    font_small = None

    for font_path in font_paths:
        try:
            font_large = ImageFont.truetype(font_path, 48)
            font_medium = ImageFont.truetype(font_path, 24)
            font_small = ImageFont.truetype(font_path, 18)
            break
        except (OSError, IOError):
            continue

    # Fall back to default font if no system fonts found
    if font_large is None:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw title
    title = script.name or "Untitled"
    draw.text((THUMBNAIL_WIDTH // 2, 100), title,
              fill=(255, 255, 255), font=font_large, anchor="mm")

    # Draw frame info
    info_text = f"Frame #{frame_info.frame_number}"
    draw.text((THUMBNAIL_WIDTH // 2, 300), info_text,
              fill=(200, 200, 200), font=font_medium, anchor="mm")

    timestamp_text = f"Timestamp: {frame_info.timestamp:.2f}s"
    draw.text((THUMBNAIL_WIDTH // 2, 350), timestamp_text,
              fill=(150, 150, 150), font=font_small, anchor="mm")

    segment_text = f"Segment: {frame_info.segment_type}"
    draw.text((THUMBNAIL_WIDTH // 2, 400), segment_text,
              fill=(150, 150, 150), font=font_small, anchor="mm")

    desc_text = frame_info.description
    if len(desc_text) > 60:
        desc_text = desc_text[:57] + "..."
    draw.text((THUMBNAIL_WIDTH // 2, 450), desc_text,
              fill=(100, 200, 255), font=font_small, anchor="mm")

    # Draw border
    draw.rectangle(
        [(10, 10), (THUMBNAIL_WIDTH - 10, THUMBNAIL_HEIGHT - 10)],
        outline=(60, 60, 80),
        width=2
    )

    # Add "PLACEHOLDER" watermark
    draw.text((THUMBNAIL_WIDTH // 2, THUMBNAIL_HEIGHT - 50), "PLACEHOLDER THUMBNAIL",
              fill=(100, 100, 100), font=font_small, anchor="mm")

    img.save(output_path, 'PNG')
    return True


def extract_thumbnails(
    script: VideoScript,
    output_dir: Path,
    strategy: str = 'evenly_spaced',
    count: int = 3,
    quiet: bool = False
) -> List[dict]:
    """Extract thumbnail frames from a video script.

    Args:
        script: VideoScript to process
        output_dir: Directory to save PNG files
        strategy: Frame selection strategy
        count: Number of frames (for evenly_spaced strategy)
        quiet: Suppress non-essential output

    Returns:
        List of metadata dictionaries for generated thumbnails
    """
    # Select frames based on strategy
    frames = select_frames(script, strategy, count)

    if not frames:
        if not quiet:
            print("No frames to extract", file=sys.stderr)
        return []

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate script name for filenames
    script_name = script.name or "script"
    # Sanitize for filename
    script_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in script_name)

    metadata = []
    for i, frame_info in enumerate(frames):
        filename = f"{script_name}_thumb_{i + 1}.png"
        output_path = output_dir / filename

        success = generate_placeholder_frame(frame_info, script, output_path)

        if success:
            meta = {
                'filename': filename,
                'path': str(output_path),
                'frame_number': frame_info.frame_number,
                'timestamp': frame_info.timestamp,
                'segment_index': frame_info.segment_index,
                'segment_type': frame_info.segment_type,
                'description': frame_info.description,
                'width': THUMBNAIL_WIDTH,
                'height': THUMBNAIL_HEIGHT,
            }
            metadata.append(meta)

            if not quiet:
                print(f"  Generated: {filename} ({frame_info.description})",
                      file=sys.stderr)

    return metadata


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog='thumbnail-extractor',
        description='Extract key frames for YouTube thumbnails from video scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.json -o thumbnails/
  %(prog)s script.json --count 5 -o thumbnails/
  %(prog)s script.json --strategy title -o thumbnails/
  cat script.json | %(prog)s - -o thumbnails/

Frame Selection Strategies:
  evenly_spaced  Distribute frames evenly across the video (default)
  title          Extract frames from title card segments only
        """
    )

    parser.add_argument(
        'input',
        help='Input video script JSON file (use - for stdin)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory for PNG files'
    )
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=3,
        help='Number of frames to extract (default: 3, used with evenly_spaced strategy)'
    )
    parser.add_argument(
        '-s', '--strategy',
        choices=['evenly_spaced', 'title'],
        default='evenly_spaced',
        help='Frame selection strategy (default: evenly_spaced)'
    )

    # Mutually exclusive verbose/quiet options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    verbosity_group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-essential output'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output metadata as JSON to stdout'
    )

    args = parser.parse_args()

    try:
        # Load script
        if args.verbose:
            print(f"Loading script: {args.input}", file=sys.stderr)

        script = load_script(args.input)

        # Validate script
        errors = script.validate()
        if errors:
            print("Error: Script has validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1

        if args.verbose:
            print(f"Script: {script.name}", file=sys.stderr)
            print(f"Duration: {script.total_duration:.1f}s", file=sys.stderr)
            print(f"Segments: {script.segment_count}", file=sys.stderr)

        # Extract thumbnails
        output_dir = Path(args.output)
        if not args.quiet:
            print(f"\nExtracting thumbnails to: {output_dir}", file=sys.stderr)
            print(f"Strategy: {args.strategy}", file=sys.stderr)
            if args.strategy == 'evenly_spaced':
                print(f"Count: {args.count}", file=sys.stderr)
            print("", file=sys.stderr)

        metadata = extract_thumbnails(
            script=script,
            output_dir=output_dir,
            strategy=args.strategy,
            count=args.count,
            quiet=args.quiet
        )

        if not metadata:
            print("Warning: No thumbnails were generated", file=sys.stderr)
            return 0

        # Write metadata JSON - sanitize script name for filename
        script_name_safe = script.name or "script"
        script_name_safe = "".join(
            c if c.isalnum() or c in '-_' else '_'
            for c in script_name_safe
        )
        metadata_file = output_dir / f"{script_name_safe}_metadata.json"
        full_metadata = {
            'script_name': script.name,
            'total_duration': script.total_duration,
            'format': script.format.name,
            'resolution': f"{THUMBNAIL_WIDTH}x{THUMBNAIL_HEIGHT}",
            'strategy': args.strategy,
            'frames': metadata
        }

        with open(metadata_file, 'w') as f:
            json.dump(full_metadata, f, indent=2)

        if not args.quiet:
            print(f"\nMetadata written to: {metadata_file}", file=sys.stderr)
            print(f"Generated {len(metadata)} thumbnail(s)", file=sys.stderr)

        # Output JSON to stdout if requested
        if args.json:
            print(json.dumps(full_metadata, indent=2))

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
