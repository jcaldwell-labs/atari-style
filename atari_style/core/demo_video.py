#!/usr/bin/env python3
"""Terminal demo video export CLI.

Renders terminal-based demos to video using scripted input and
headless rendering.

Usage:
    python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json -o output.mp4
    python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --preview

Supported demos:
    joystick_test - Joystick verification interface
    (more to be added)
"""

import os
import sys
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

from .scripted_input import ScriptedInputHandler, InputScript
from .headless_renderer import HeadlessRenderer, HeadlessRendererFactory


# Registry of demos that support video export
DEMO_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_demo(name: str, factory: Callable, description: str = ""):
    """Register a demo for video export.

    Args:
        name: Demo identifier (used in CLI)
        factory: Function(renderer, input_handler) -> demo instance
        description: Human-readable description
    """
    DEMO_REGISTRY[name] = {
        'factory': factory,
        'description': description,
    }


class JoystickTestDemo:
    """Headless-compatible joystick test demo."""

    def __init__(self, renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
        self.renderer = renderer
        self.input_handler = input_handler

    def draw_crosshair(self, cx: int, cy: int, x: float, y: float):
        """Draw joystick position crosshair."""
        # Draw center reference
        self.renderer.draw_text(cx - 1, cy, '┼', 'yellow')

        # Draw axes
        for i in range(-20, 21):
            if 0 <= cx + i < self.renderer.width:
                self.renderer.set_pixel(cx + i, cy, '─', 'cyan')
            if 0 <= cy + i // 2 < self.renderer.height:
                self.renderer.set_pixel(cx, cy + i // 2, '│', 'cyan')

        # Draw current position
        pos_x = int(cx + x * 20)
        pos_y = int(cy + y * 10)
        if 0 <= pos_x < self.renderer.width and 0 <= pos_y < self.renderer.height:
            self.renderer.set_pixel(pos_x, pos_y, '●', 'bright_green')

            # Draw line from center to position
            steps = 20
            for i in range(steps):
                t = i / steps
                lx = int(cx + x * 20 * t)
                ly = int(cy + y * 10 * t)
                if 0 <= lx < self.renderer.width and 0 <= ly < self.renderer.height:
                    self.renderer.set_pixel(lx, ly, '·', 'green')

    def draw_button_indicator(self, x: int, y: int, button_num: int, pressed: bool):
        """Draw a button state indicator."""
        color = 'bright_green' if pressed else 'white'
        char = '█' if pressed else '□'
        self.renderer.draw_text(x, y, f"BTN {button_num}: {char}", color)

    def draw(self):
        """Render the joystick test interface."""
        self.renderer.clear_buffer()

        # Draw title
        title = "JOYSTICK VERIFICATION"
        self.renderer.draw_text((self.renderer.width - len(title)) // 2, 2, title, 'bright_cyan')

        # Get joystick info
        info = self.input_handler.verify_joystick()

        # Connection status
        status = f"CONNECTED: {info['name']}"
        self.renderer.draw_text((self.renderer.width - len(status)) // 2, 4, status, 'bright_green')

        # Draw joystick state
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2

        # Get current axis values
        x, y = self.input_handler.get_joystick_state()

        # Draw crosshair
        self.draw_crosshair(cx, cy, x, y)

        # Draw axis values
        self.renderer.draw_text(5, 8, f"X Axis: {x:+.2f}", 'yellow')
        self.renderer.draw_text(5, 9, f"Y Axis: {y:+.2f}", 'yellow')

        # Draw button states (Hyperkin Trooper V2 has 6 buttons)
        buttons = self.input_handler.get_joystick_buttons()
        button_y = 11
        for i in range(6):  # Only 6 buttons on Hyperkin Trooper V2
            self.draw_button_indicator(5, button_y + i, i, buttons.get(i, False))

        # Draw info
        self.renderer.draw_text(5, 6, f"Axes: {info['axes']}", 'cyan')
        self.renderer.draw_text(5, 7, f"Buttons: 6", 'cyan')  # Hyperkin has 6 buttons

        # Draw visual button panel on right - Hyperkin Trooper V2 layout
        if buttons:
            panel_x = self.renderer.width - 28
            panel_y = 8
            self.renderer.draw_text(panel_x, panel_y, "BUTTON PANEL", 'magenta')
            self.renderer.draw_text(panel_x, panel_y + 1, "(Hyperkin Trooper V2)", 'cyan')

            # Face buttons (0, 1) - circles ● ○
            self.renderer.draw_text(panel_x, panel_y + 3, "Face:", 'yellow')
            for i in range(2):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '●' if pressed else '○'  # Circle buttons
                self.renderer.draw_text(panel_x + 6 + i * 4, panel_y + 3, f"{i}:{char}", color)

            # Shoulder buttons (2, 3, 4, 5) - rectangles ■ □
            # Front pair (2, 3)
            self.renderer.draw_text(panel_x, panel_y + 5, "Front:", 'yellow')
            for idx, i in enumerate([2, 3]):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '■' if pressed else '□'  # Rectangle buttons
                self.renderer.draw_text(panel_x + 7 + idx * 4, panel_y + 5, f"{i}:{char}", color)

            # Rear pair (4, 5)
            self.renderer.draw_text(panel_x, panel_y + 7, "Rear:", 'yellow')
            for idx, i in enumerate([4, 5]):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '■' if pressed else '□'  # Rectangle buttons
                self.renderer.draw_text(panel_x + 7 + idx * 4, panel_y + 7, f"{i}:{char}", color)

        # Draw instructions
        instructions = [
            "Move joystick to test axes",
            "Press ALL buttons to test",
            "Demo video - scripted input"
        ]
        for i, text in enumerate(instructions):
            self.renderer.draw_text((self.renderer.width - len(text)) // 2,
                                    self.renderer.height - 5 + i, text, 'cyan')


def create_joystick_test(renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
    """Factory for JoystickTestDemo."""
    return JoystickTestDemo(renderer, input_handler)


# Register built-in demos
register_demo('joystick_test', create_joystick_test, 'Joystick verification interface')


class DemoVideoExporter:
    """Exports terminal demos to video using scripted input."""

    def __init__(
        self,
        demo_name: str,
        script_path: str,
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        char_columns: int = 100,
        char_rows: int = 40,
    ):
        """Initialize exporter.

        Args:
            demo_name: Name of demo to render (from registry)
            script_path: Path to input script JSON
            output_path: Output video file path
            width: Output video width in pixels
            height: Output video height in pixels
            char_columns: Terminal columns
            char_rows: Terminal rows
        """
        if demo_name not in DEMO_REGISTRY:
            available = ', '.join(DEMO_REGISTRY.keys())
            raise ValueError(f"Unknown demo '{demo_name}'. Available: {available}")

        self.demo_name = demo_name
        self.script_path = script_path
        self.output_path = output_path

        # Load script
        self.script = InputScript.from_file(script_path)

        # Create renderer with target resolution
        self.renderer = HeadlessRendererFactory.for_resolution(
            width, height, char_columns, char_rows
        )

        # Create scripted input handler
        self.input_handler = ScriptedInputHandler(script=self.script)

        # Create demo instance
        factory = DEMO_REGISTRY[demo_name]['factory']
        self.demo = factory(self.renderer, self.input_handler)

    def export(self, progress_callback: Optional[Callable[[int, int], None]] = None):
        """Export demo to video.

        Args:
            progress_callback: Optional callback(current_frame, total_frames)
        """
        total_frames = self.input_handler.get_frame_count()
        frame_time = 1.0 / self.script.fps

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix='atari_demo_')

        try:
            # Start script playback
            self.input_handler.start()

            # Render each frame
            for frame_num in range(total_frames):
                # Update input handler time
                self.input_handler.current_time = frame_num * frame_time

                # Render frame
                self.demo.draw()

                # Save frame
                frame_path = os.path.join(temp_dir, f'frame_{frame_num:05d}.png')
                self.renderer.save_frame(frame_path)

                if progress_callback:
                    progress_callback(frame_num + 1, total_frames)

            # Encode video with ffmpeg
            self._encode_video(temp_dir)

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _encode_video(self, frames_dir: str):
        """Encode frames to video using ffmpeg."""
        # Check for ffmpeg
        if not shutil.which('ffmpeg'):
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        frame_pattern = os.path.join(frames_dir, 'frame_%05d.png')

        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(self.script.fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            self.output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    def preview_frame(self, time: float) -> 'Image.Image':
        """Render a single frame at the given time.

        Args:
            time: Time in seconds

        Returns:
            PIL Image of the frame
        """
        self.input_handler.current_time = time
        self.demo.draw()
        return self.renderer.to_image()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export terminal demos to video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s joystick_test scripts/demos/joystick-demo.json -o joystick-demo.mp4
  %(prog)s joystick_test scripts/demos/joystick-demo.json --preview
  %(prog)s --list

Available demos:
""" + '\n'.join(f"  {name}: {info['description']}" for name, info in DEMO_REGISTRY.items())
    )

    parser.add_argument('demo', nargs='?', help='Demo name to render')
    parser.add_argument('script', nargs='?', help='Path to input script JSON')
    parser.add_argument('-o', '--output', help='Output video file path')
    parser.add_argument('--width', type=int, default=1920, help='Output width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Output height (default: 1080)')
    parser.add_argument('--columns', type=int, default=100, help='Terminal columns (default: 100)')
    parser.add_argument('--rows', type=int, default=40, help='Terminal rows (default: 40)')
    parser.add_argument('--preview', action='store_true', help='Show preview of middle frame')
    parser.add_argument('--list', action='store_true', help='List available demos')

    args = parser.parse_args()

    if args.list:
        print("Available demos:")
        for name, info in DEMO_REGISTRY.items():
            print(f"  {name}: {info['description']}")
        return

    if not args.demo or not args.script:
        parser.error("demo and script arguments are required")

    # Determine output path
    output_path = args.output
    if not output_path:
        script_stem = Path(args.script).stem
        output_path = f"{args.demo}-{script_stem}.mp4"

    try:
        exporter = DemoVideoExporter(
            demo_name=args.demo,
            script_path=args.script,
            output_path=output_path,
            width=args.width,
            height=args.height,
            char_columns=args.columns,
            char_rows=args.rows,
        )

        if args.preview:
            # Show preview of middle frame
            duration = exporter.script.duration
            img = exporter.preview_frame(duration / 2)
            preview_path = f"{args.demo}-preview.png"
            img.save(preview_path)
            print(f"Preview saved to: {preview_path}")
            return

        # Export video with progress
        def show_progress(current, total):
            pct = current * 100 // total
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\rRendering: [{bar}] {pct}% ({current}/{total} frames)", end='', flush=True)

        print(f"Exporting {args.demo} demo...")
        print(f"Script: {args.script}")
        print(f"Output: {output_path}")
        print(f"Duration: {exporter.script.duration}s @ {exporter.script.fps}fps")
        print()

        exporter.export(progress_callback=show_progress)

        print()
        print(f"✓ Video exported to: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
