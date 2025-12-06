#!/usr/bin/env python3
"""YouTube Chapter Markers - Export chapter markers from video scripts.

Generate YouTube-compatible chapter markers from video scripts. Each segment
with type "title" becomes a chapter marker with its text as the chapter title.

Usage:
    python -m atari_style.tools.chapter_markers script.json
    python -m atari_style.tools.chapter_markers script.json -o chapters.txt
    python -m atari_style.tools.chapter_markers script.json --json
    cat script.json | python -m atari_style.tools.chapter_markers -

Examples:
    # Output chapter markers to stdout (default text format)
    python -m atari_style.tools.chapter_markers scripts/videos/lissajous-intro.json

    # Write to file
    python -m atari_style.tools.chapter_markers scripts/videos/lissajous-intro.json -o chapters.txt

    # Output as JSON
    python -m atari_style.tools.chapter_markers scripts/videos/lissajous-intro.json --json

    # Include all segments (not just title segments)
    python -m atari_style.tools.chapter_markers scripts/videos/lissajous-intro.json --include-all

    # Read from stdin (pipeline support)
    cat script.json | python -m atari_style.tools.chapter_markers -
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..core.video_script import (
    VideoScript,
    Segment,
    TitleSegment,
    SegmentType,
    VisualizationSegment,
    SweepSegment,
    TransitionSegment,
    PauseSegment,
)

# Duration threshold for switching to H:MM:SS format (1 hour)
HOUR_THRESHOLD_SECONDS = 3600


@dataclass
class Chapter:
    """A chapter marker with timestamp and label."""
    timestamp: float  # Start time in seconds
    label: str  # Chapter title/description


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


def format_timestamp(seconds: float, use_hours: bool = False) -> str:
    """Format seconds as YouTube timestamp (M:SS or H:MM:SS).

    Args:
        seconds: Time in seconds
        use_hours: If True, always use H:MM:SS format

    Returns:
        Formatted timestamp string
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if use_hours or hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def get_segment_label(segment: Segment) -> str:
    """Generate a label for a segment.

    Args:
        segment: A video script segment

    Returns:
        Human-readable label for the segment
    """
    seg_type = segment.get_type()

    if seg_type == SegmentType.TITLE:
        if isinstance(segment, TitleSegment):
            return segment.text
        return "Title"
    elif seg_type == SegmentType.VISUALIZATION:
        if isinstance(segment, VisualizationSegment):
            return f"Visualization: {segment.visualizer}"
        return "Visualization"
    elif seg_type == SegmentType.SWEEP:
        if isinstance(segment, SweepSegment):
            return f"Parameter Sweep: {segment.visualizer}"
        return "Parameter Sweep"
    elif seg_type == SegmentType.TRANSITION:
        if isinstance(segment, TransitionSegment):
            return f"Transition: {segment.effect}"
        return "Transition"
    elif seg_type == SegmentType.PAUSE:
        return "Pause"
    else:
        return f"Segment ({seg_type.value})"


def extract_chapters(
    script: VideoScript,
    include_all: bool = False
) -> List[Chapter]:
    """Extract chapter markers from a video script.

    Args:
        script: VideoScript to process
        include_all: If True, include all segments (not just title segments)

    Returns:
        List of Chapter objects with timestamps and labels
    """
    if not script.segments:
        return []

    chapters = []
    current_time = 0.0

    for segment in script.segments:
        seg_type = segment.get_type()

        # Include only title segments by default, or all if include_all
        if include_all or seg_type == SegmentType.TITLE:
            label = get_segment_label(segment)
            chapters.append(Chapter(timestamp=current_time, label=label))

        current_time += segment.duration

    return chapters


def format_chapters_text(chapters: List[Chapter], total_duration: float) -> str:
    """Format chapters as YouTube description text.

    Args:
        chapters: List of Chapter objects
        total_duration: Total video duration (for timestamp format decision)

    Returns:
        YouTube chapter format string (one chapter per line)
    """
    if not chapters:
        return ""

    use_hours = total_duration >= HOUR_THRESHOLD_SECONDS
    lines = []

    for chapter in chapters:
        timestamp = format_timestamp(chapter.timestamp, use_hours)
        lines.append(f"{timestamp} {chapter.label}")

    return "\n".join(lines)


def format_chapters_json(chapters: List[Chapter]) -> str:
    """Format chapters as JSON.

    Args:
        chapters: List of Chapter objects

    Returns:
        JSON string with chapters array
    """
    data = {
        "chapters": [
            {"timestamp": int(ch.timestamp), "label": ch.label}
            for ch in chapters
        ]
    }
    return json.dumps(data, indent=2)


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog='chapter-markers',
        description='Export YouTube chapter markers from video scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.json              # Output to stdout (text format)
  %(prog)s script.json -o chapters.txt  # Output to file
  %(prog)s script.json --json       # Output as JSON
  %(prog)s script.json --include-all    # Include all segments
  cat script.json | %(prog)s -      # Read from stdin

Output Formats:
  text (default)  YouTube description format (M:SS Label or H:MM:SS Label)
  json            Structured JSON for programmatic use
        """
    )

    parser.add_argument(
        'input',
        help='Input video script JSON file (use - for stdin)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON format instead of text'
    )
    parser.add_argument(
        '--include-all',
        action='store_true',
        help='Include non-title segments (visualizations, transitions) as chapters'
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

        # Extract chapters
        chapters = extract_chapters(script, include_all=args.include_all)

        if not chapters:
            if not args.quiet:
                print("Warning: No chapters found in script", file=sys.stderr)

        if args.verbose:
            print(f"Chapters found: {len(chapters)}", file=sys.stderr)

        # Format output
        if args.json:
            output = format_chapters_json(chapters)
        else:
            output = format_chapters_text(chapters, script.total_duration)

        # Write output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output)
                if output:
                    f.write('\n')
            if not args.quiet:
                print(f"Output written to: {args.output}", file=sys.stderr)
        else:
            if output:
                print(output)

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
