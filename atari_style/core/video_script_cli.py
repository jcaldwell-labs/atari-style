#!/usr/bin/env python3
"""Video Script CLI - Execute declarative video scripts.

A command-line tool for validating, previewing, and rendering
video scripts defined in JSON format.

Usage:
    python -m atari_style.core.video_script_cli validate script.json
    python -m atari_style.core.video_script_cli info script.json
    python -m atari_style.core.video_script_cli render script.json -o output.mp4
    python -m atari_style.core.video_script_cli list-formats

Examples:
    # Validate a script
    python -m atari_style.core.video_script_cli validate scripts/videos/lissajous-intro.json

    # Show script information
    python -m atari_style.core.video_script_cli info scripts/videos/lissajous-intro.json

    # Read from stdin
    cat script.json | python -m atari_style.core.video_script_cli validate -

    # Render to video
    python -m atari_style.core.video_script_cli render scripts/videos/lissajous-intro.json -o intro.mp4

    # List available format presets
    python -m atari_style.core.video_script_cli list-formats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

from .video_script import (
    VideoScript, FORMAT_PRESETS,
    TitleSegment, VisualizationSegment, SweepSegment,
    TransitionSegment, PauseSegment
)


def load_script(script_arg: str) -> Tuple[VideoScript, str]:
    """Load a video script from file or stdin.

    Args:
        script_arg: Path to script file, or '-' for stdin

    Returns:
        Tuple of (VideoScript, source_name)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        Exception: Other loading errors
    """
    if script_arg == '-':
        # Read from stdin
        data = json.load(sys.stdin)
        return VideoScript.from_dict(data), '<stdin>'
    else:
        # Read from file
        script_path = Path(script_arg)
        if not script_path.exists():
            raise FileNotFoundError(script_path)
        return VideoScript.from_file(script_path), str(script_path)


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a video script file.

    Returns:
        0 if valid, 1 if invalid
    """
    try:
        script, source = load_script(args.script)
        errors = script.validate()

        if errors:
            print(f"❌ Script '{script.name}' has {len(errors)} error(s):\n")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            return 1
        else:
            print(f"✓ Script '{script.name}' is valid")
            print(f"  Duration: {script.total_duration:.1f}s")
            print(f"  Segments: {script.segment_count}")
            print(f"  Format: {script.format.name} ({script.format.width}x{script.format.height})")
            return 0

    except FileNotFoundError as e:
        print(f"Error: Script file not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error loading script: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display detailed information about a video script."""
    try:
        script, source = load_script(args.script)

        # Header
        print(f"\n{'═' * 60}")
        print(f"  VIDEO SCRIPT: {script.name}")
        print(f"{'═' * 60}\n")

        # Metadata
        print("METADATA:")
        print(f"  Version:     {script.version}")
        print(f"  Author:      {script.author or '(not specified)'}")
        print(f"  Description: {script.description or '(not specified)'}")
        print()

        # Format
        print("FORMAT:")
        print(f"  Preset:      {script.format.name}")
        print(f"  Resolution:  {script.format.width}x{script.format.height}")
        print(f"  FPS:         {script.format.fps}")
        print(f"  Aspect:      {script.format.aspect_ratio}")
        if script.format.max_duration:
            print(f"  Max Duration: {script.format.max_duration}s")
        print()

        # Duration
        print("TIMING:")
        print(f"  Total Duration: {script.total_duration:.1f}s")
        total_frames = int(script.total_duration * script.format.fps)
        print(f"  Total Frames:   {total_frames}")
        print()

        # Segments
        print(f"SEGMENTS ({script.segment_count}):")
        print(f"  {'#':<3} {'Type':<14} {'Duration':<10} {'Details'}")
        print(f"  {'-' * 3} {'-' * 14} {'-' * 10} {'-' * 30}")

        time_offset = 0.0
        for i, seg in enumerate(script.segments, 1):
            seg_type = seg.get_type().value.upper()
            duration_str = f"{seg.duration:.1f}s"

            if isinstance(seg, TitleSegment):
                details = f'"{seg.text}"'
                if seg.subtitle:
                    details += f' - {seg.subtitle}'
            elif isinstance(seg, VisualizationSegment):
                params_str = ', '.join(f"{k}={v}" for k, v in list(seg.params.items())[:3])
                details = f'{seg.visualizer}: {params_str}'
            elif isinstance(seg, SweepSegment):
                details = f'{seg.visualizer}: {seg.easing.value} sweep'
            elif isinstance(seg, TransitionSegment):
                details = f'{seg.effect} effect'
            elif isinstance(seg, PauseSegment):
                details = 'hold frame'
            else:
                details = ''

            # Truncate details if too long
            if len(details) > 35:
                details = details[:32] + '...'

            print(f"  {i:<3} {seg_type:<14} {duration_str:<10} {details}")
            time_offset += seg.duration

        print()

        # Validation
        errors = script.validate()
        if errors:
            print(f"VALIDATION: ❌ {len(errors)} error(s)")
            for error in errors:
                print(f"  - {error}")
        else:
            print("VALIDATION: ✓ Valid")

        print()
        return 0

    except FileNotFoundError as e:
        print(f"Error: Script file not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error loading script: {e}", file=sys.stderr)
        return 1


def cmd_render(args: argparse.Namespace) -> int:
    """Render a video script to video file."""
    try:
        script, source = load_script(args.script)

        # Validate first
        errors = script.validate()
        if errors:
            print("Error: Script has validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1

        # Determine output path
        output_path = args.output
        if not output_path:
            output_path = f"{script.name}.mp4"

        # Display rendering plan
        print(f"\n{'═' * 60}")
        print(f"  RENDERING: {script.name}")
        print(f"{'═' * 60}\n")
        print(f"Script:     {source}")
        print(f"Output:     {output_path}")
        print(f"Format:     {script.format.name} ({script.format.width}x{script.format.height} @ {script.format.fps}fps)")
        print(f"Duration:   {script.total_duration:.1f}s")
        print(f"Segments:   {script.segment_count}")

        total_frames = int(script.total_duration * script.format.fps)
        print(f"Frames:     {total_frames}")
        print()

        if args.dry_run:
            print("(Dry run - no video will be rendered)")
            return 0

        # Segment rendering is planned for Issue #30 Phase 2
        # The schema and CLI validation are complete (Phase 1)
        # Rendering requires implementing segment-specific renderers
        # that connect to the existing VideoExporter infrastructure
        print("⚠️  Video rendering is not yet implemented.")
        print()
        print("The video script CLI currently supports:")
        print("  - validate: Check script for errors")
        print("  - info: Display script information")
        print("  - list-formats: Show available format presets")
        print()
        print("Rendering will be implemented in Issue #30 Phase 2.")
        print("For now, you can use the demo_video.py module for rendering demos.")

        return 0

    except FileNotFoundError as e:
        print(f"Error: Script file not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list_formats(args: argparse.Namespace) -> int:
    """List available format presets."""
    print("\n" + "═" * 60)
    print("  AVAILABLE FORMAT PRESETS")
    print("═" * 60 + "\n")

    # Group by orientation
    vertical = []
    horizontal = []
    square = []

    for name, fmt in FORMAT_PRESETS.items():
        entry = (name, fmt)
        if fmt.is_square:
            square.append(entry)
        elif fmt.is_vertical:
            vertical.append(entry)
        else:
            horizontal.append(entry)

    def print_format(name: str, fmt) -> None:
        limit_str = f" (max {fmt.max_duration}s)" if fmt.max_duration else ""
        print(f"  {name:<20} {fmt.width}x{fmt.height} @ {fmt.fps}fps{limit_str}")
        if fmt.description:
            print(f"  {' ' * 20} {fmt.description}")

    if horizontal:
        print("LANDSCAPE (16:9):")
        for name, fmt in horizontal:
            print_format(name, fmt)
        print()

    if vertical:
        print("PORTRAIT (9:16):")
        for name, fmt in vertical:
            print_format(name, fmt)
        print()

    if square:
        print("SQUARE (1:1):")
        for name, fmt in square:
            print_format(name, fmt)
        print()

    print("Usage in scripts:")
    print('  {"format": "youtube_landscape", ...}')
    print()

    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='video-script',
        description='Video Script CLI - Execute declarative video scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  video-script validate scripts/videos/lissajous-intro.json
  video-script info scripts/videos/lissajous-intro.json
  video-script render scripts/videos/lissajous-intro.json -o intro.mp4
  video-script list-formats

  # Read from stdin (Unix pipeline support)
  cat script.json | video-script validate -
  echo '{"name":"test",...}' | video-script info -

For more information, see:
  https://github.com/jcaldwell-labs/atari-style
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate a video script file'
    )
    validate_parser.add_argument('script', help='Path to script JSON file (use - for stdin)')

    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Display detailed information about a video script'
    )
    info_parser.add_argument('script', help='Path to script JSON file (use - for stdin)')

    # render command
    render_parser = subparsers.add_parser(
        'render',
        help='Render a video script to video file'
    )
    render_parser.add_argument('script', help='Path to script JSON file (use - for stdin)')
    render_parser.add_argument('-o', '--output', help='Output video file path')
    render_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rendered without actually rendering'
    )
    render_parser.add_argument(
        '--format',
        help='Override format preset (e.g., youtube_shorts)'
    )

    # list-formats command
    subparsers.add_parser(
        'list-formats',
        help='List available format presets'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    if args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'render':
        return cmd_render(args)
    elif args.command == 'list-formats':
        return cmd_list_formats(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
