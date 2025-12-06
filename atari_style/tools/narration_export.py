#!/usr/bin/env python3
"""Narration Timestamp Export - Export timestamp markers and narration cues.

Export timestamp markers and narration cues from video scripts for voiceover
production. Supports JSON and markdown output formats.

Usage:
    python -m atari_style.tools.narration_export script.json
    python -m atari_style.tools.narration_export script.json -o narration.json
    python -m atari_style.tools.narration_export script.json --markdown -o narration.md
    cat script.json | python -m atari_style.tools.narration_export -

Examples:
    # Output JSON to stdout
    python -m atari_style.tools.narration_export scripts/videos/lissajous-intro.json

    # Output JSON to file
    python -m atari_style.tools.narration_export scripts/videos/lissajous-intro.json -o narration.json

    # Output markdown format
    python -m atari_style.tools.narration_export scripts/videos/lissajous-intro.json --markdown

    # Read from stdin (pipeline support)
    cat script.json | python -m atari_style.tools.narration_export - --markdown
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
    VisualizationSegment,
    SweepSegment,
    TransitionSegment,
    PauseSegment,
)


@dataclass
class NarrationMarker:
    """A single narration marker with timestamp and cue information."""
    time: float
    event: str
    segment_type: str
    cue: str


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


def format_time_display(seconds: float) -> str:
    """Format time in seconds to M:SS display format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string like "0:00" or "1:23"
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def generate_markers(script: VideoScript) -> List[NarrationMarker]:
    """Generate narration markers from video script segments.

    Creates a marker at the start of each segment with appropriate
    event type and cue text based on segment content.

    Args:
        script: VideoScript to process

    Returns:
        List of NarrationMarker objects in chronological order
    """
    markers = []
    current_time = 0.0

    for segment in script.segments:
        marker = None

        if isinstance(segment, TitleSegment):
            marker = NarrationMarker(
                time=current_time,
                event="title_card",
                segment_type="title",
                cue=segment.text
            )
        elif isinstance(segment, VisualizationSegment):
            # Build cue with visualizer name and key params
            params_str = ""
            if segment.params:
                param_items = [f"{k}={v}" for k, v in segment.params.items()]
                params_str = f" ({', '.join(param_items)})"

            marker = NarrationMarker(
                time=current_time,
                event="visualization_start",
                segment_type="visualization",
                cue=f"Visualizer: {segment.visualizer}{params_str}"
            )
        elif isinstance(segment, SweepSegment):
            # Note the parameter sweep range
            from_items = [f"{k}={v}" for k, v in segment.from_params.items()]
            to_items = [f"{k}={v}" for k, v in segment.to_params.items()]
            from_str = ", ".join(from_items)
            to_str = ", ".join(to_items)

            marker = NarrationMarker(
                time=current_time,
                event="sweep_start",
                segment_type="sweep",
                cue=f"Sweep: {segment.visualizer} from ({from_str}) to ({to_str})"
            )
        elif isinstance(segment, TransitionSegment):
            marker = NarrationMarker(
                time=current_time,
                event="transition",
                segment_type="transition",
                cue=f"Transition: {segment.effect}"
            )
        elif isinstance(segment, PauseSegment):
            marker = NarrationMarker(
                time=current_time,
                event="pause",
                segment_type="pause",
                cue=f"Pause for {segment.duration:.1f}s"
            )

        if marker:
            markers.append(marker)

        current_time += segment.duration

    return markers


def format_json_output(script: VideoScript, markers: List[NarrationMarker]) -> str:
    """Format markers as JSON output.

    Args:
        script: VideoScript for metadata
        markers: List of NarrationMarker objects

    Returns:
        JSON string with script metadata and markers
    """
    output = {
        "script_name": script.name,
        "total_duration": script.total_duration,
        "markers": [
            {
                "time": m.time,
                "event": m.event,
                "segment_type": m.segment_type,
                "cue": m.cue
            }
            for m in markers
        ]
    }
    return json.dumps(output, indent=2)


def format_markdown_output(script: VideoScript, markers: List[NarrationMarker]) -> str:
    """Format markers as markdown output.

    Args:
        script: VideoScript for metadata
        markers: List of NarrationMarker objects

    Returns:
        Markdown string with timeline table
    """
    lines = [
        f"# Narration Guide: {script.name}",
        f"Total Duration: {script.total_duration:.1f}s",
        "",
        "## Timeline",
        "",
        "| Time | Event | Cue |",
        "|------|-------|-----|"
    ]

    for marker in markers:
        time_str = format_time_display(marker.time)
        # Format event name as title case with spaces
        event_display = marker.event.replace("_", " ").title()
        # Quote the cue text for markdown readability
        cue_display = f'"{marker.cue}"'
        lines.append(f"| {time_str} | {event_display} | {cue_display} |")

    lines.append("")  # Trailing newline
    return "\n".join(lines)


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog='narration-export',
        description='Export timestamp markers and narration cues from video scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.json                    # Output JSON to stdout
  %(prog)s script.json -o narration.json  # Output JSON to file
  %(prog)s script.json --markdown         # Output markdown format
  cat script.json | %(prog)s -            # Read from stdin

Output Formats:
  JSON (default)  Structured output for programmatic use
  Markdown        Human-readable narration guide with timeline table
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
        '--markdown',
        action='store_true',
        help='Output markdown format instead of JSON'
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

        # Generate markers
        markers = generate_markers(script)

        if args.verbose:
            print(f"Generated {len(markers)} markers", file=sys.stderr)

        # Format output
        if args.markdown:
            output = format_markdown_output(script, markers)
        else:
            output = format_json_output(script, markers)

        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            if not args.quiet:
                print(f"Output written to: {args.output}", file=sys.stderr)
        else:
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
