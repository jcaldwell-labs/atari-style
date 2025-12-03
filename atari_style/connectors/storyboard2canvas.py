#!/usr/bin/env python3
"""Convert atari-style storyboards to boxes-live canvas format.

Usage:
    python -m atari_style.connectors.storyboard2canvas storyboard.json > canvas.txt
    python -m atari_style.connectors.storyboard2canvas storyboard.json -o canvas.txt
    python -m atari_style.connectors.storyboard2canvas storyboard.json | boxes-live --load -

Output Format:
    BOXES_CANVAS_V1
    <world_width> <world_height>
    <box_count>
    <box_data>...

Each keyframe becomes a box with:
- Position: Arranged horizontally by time
- Title: Keyframe ID
- Content: Parameters, time, note
- Color: Based on parameter intensity
- Connections shown via position flow
"""

import sys
import json
import argparse
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CanvasBox:
    """Represents a box in the canvas."""
    id: int
    x: float
    y: float
    width: int
    height: int
    selected: int
    color: int
    title: str
    content: List[str]


class StoryboardConverter:
    """Convert storyboard JSON to boxes-live canvas format."""

    # Canvas dimensions
    WORLD_WIDTH = 2000
    WORLD_HEIGHT = 800

    # Box dimensions
    BOX_WIDTH = 28
    BOX_HEIGHT = 10

    # Layout settings
    START_X = 80
    START_Y = 150
    HORIZONTAL_SPACING = 280

    # Color mapping based on intensity
    COLORS = {
        'low': 4,      # Blue - calm
        'medium': 2,   # Green - balanced
        'high': 3,     # Yellow - energetic
        'peak': 1,     # Red - intense
    }

    def __init__(self):
        self.boxes: List[CanvasBox] = []

    def load_storyboard(self, path: str) -> Dict[str, Any]:
        """Load storyboard JSON file."""
        with open(path, 'r') as f:
            return json.load(f)

    def calculate_intensity(self, params: List[float]) -> str:
        """Calculate intensity level from parameters."""
        avg = sum(params) / len(params) if params else 0
        if avg < 0.3:
            return 'low'
        elif avg < 0.5:
            return 'medium'
        elif avg < 0.7:
            return 'high'
        else:
            return 'peak'

    def format_params(self, params: List[float]) -> str:
        """Format parameters for display."""
        return '[' + ', '.join(f'{p:.2f}' for p in params) + ']'

    def create_header_box(self, storyboard: Dict[str, Any]) -> CanvasBox:
        """Create header box with storyboard metadata."""
        title = storyboard.get('title', 'Storyboard')
        content = [
            f"Composite: {storyboard.get('composite', 'unknown')}",
            f"Format: {storyboard.get('format', 'video')}",
            f"FPS: {storyboard.get('fps', 30)}",
            f"Keyframes: {len(storyboard.get('keyframes', []))}",
        ]

        if 'description' in storyboard:
            # Word-wrap description
            desc = storyboard['description']
            if len(desc) > 50:
                content.append(desc[:47] + '...')
            else:
                content.append(desc)

        return CanvasBox(
            id=1,
            x=self.START_X,
            y=50,
            width=self.BOX_WIDTH + 10,
            height=8,
            selected=0,
            color=6,  # Cyan for header
            title=title[:40],
            content=content
        )

    def create_keyframe_box(self, keyframe: Dict[str, Any],
                            index: int, box_id: int) -> CanvasBox:
        """Create box for a keyframe."""
        kf_id = keyframe.get('id', f'kf_{index}')
        time = keyframe.get('time', 0.0)
        params = keyframe.get('params', [])
        note = keyframe.get('note', '')

        # Calculate position (horizontal flow)
        x = self.START_X + (index * self.HORIZONTAL_SPACING)
        y = self.START_Y

        # Determine color from intensity
        intensity = self.calculate_intensity(params)
        color = self.COLORS.get(intensity, 2)

        # Build content
        content = [
            f"Time: {time:.1f}s",
            f"Params: {self.format_params(params)}",
        ]

        if note:
            # Word-wrap note
            if len(note) > 45:
                content.append(note[:42] + '...')
            else:
                content.append(note)

        return CanvasBox(
            id=box_id,
            x=x,
            y=y,
            width=self.BOX_WIDTH,
            height=self.BOX_HEIGHT,
            selected=0,
            color=color,
            title=kf_id[:25],
            content=content
        )

    def convert(self, storyboard: Dict[str, Any]) -> List[CanvasBox]:
        """Convert storyboard to canvas boxes."""
        self.boxes = []

        # Add header box
        header = self.create_header_box(storyboard)
        self.boxes.append(header)

        # Add keyframe boxes
        keyframes = storyboard.get('keyframes', [])
        for idx, kf in enumerate(keyframes):
            box = self.create_keyframe_box(kf, idx, idx + 2)
            self.boxes.append(box)

        return self.boxes

    def to_canvas_format(self) -> str:
        """Generate boxes-live canvas format string."""
        lines = []

        # Header
        lines.append("BOXES_CANVAS_V1")
        lines.append(f"{self.WORLD_WIDTH} {self.WORLD_HEIGHT}")
        lines.append(str(len(self.boxes)))

        # Boxes
        for box in self.boxes:
            # Box header line
            lines.append(
                f"{box.id} {box.x} {box.y} {box.width} {box.height} "
                f"{box.selected} {box.color}"
            )
            # Title
            lines.append(box.title)
            # Content
            lines.append(str(len(box.content)))
            for content_line in box.content:
                lines.append(content_line)

        return '\n'.join(lines)


def storyboard_to_canvas(storyboard_path: str,
                         output_path: Optional[str] = None) -> str:
    """Convert storyboard file to canvas format.

    Args:
        storyboard_path: Path to storyboard JSON file
        output_path: Optional output path (None for stdout)

    Returns:
        Canvas format string
    """
    converter = StoryboardConverter()
    storyboard = converter.load_storyboard(storyboard_path)
    converter.convert(storyboard)
    canvas = converter.to_canvas_format()

    if output_path:
        with open(output_path, 'w') as f:
            f.write(canvas)

    return canvas


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert atari-style storyboard to boxes-live canvas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s storyboards/plasma-lissajous-short.json
  %(prog)s storyboards/plasma-lissajous-short.json -o storyboard.canvas
  %(prog)s storyboards/plasma-lissajous-short.json | boxes-live --load -
        """
    )
    parser.add_argument('storyboard',
                        help='Path to storyboard JSON file')
    parser.add_argument('-o', '--output',
                        help='Output file (default: stdout)')
    parser.add_argument('--width', type=int, default=2000,
                        help='Canvas world width (default: 2000)')
    parser.add_argument('--height', type=int, default=800,
                        help='Canvas world height (default: 800)')

    args = parser.parse_args()

    try:
        converter = StoryboardConverter()
        converter.WORLD_WIDTH = args.width
        converter.WORLD_HEIGHT = args.height

        storyboard = converter.load_storyboard(args.storyboard)
        converter.convert(storyboard)
        canvas = converter.to_canvas_format()

        if args.output:
            with open(args.output, 'w') as f:
                f.write(canvas)
            print(f"Canvas written to: {args.output}", file=sys.stderr)
        else:
            print(canvas)

    except FileNotFoundError:
        print(f"Error: File not found: {args.storyboard}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
