#!/usr/bin/env python3
"""Input script recorder for demo video generation.

Records live joystick input and saves it as a JSON script file
compatible with the demo video export system.

Usage:
    python -m atari_style.core.input_recorder --duration 15 --fps 30 -o my-recording.json

Options:
    --duration    Recording length in seconds
    --fps         Sample rate (default 30)
    --digital     Quantize analog to -1/0/1 for digital sticks
    --sparse      Only save keyframes on state changes
    -o            Output JSON file
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .input_handler import InputHandler


@dataclass
class RecordedKeyframe:
    """A recorded keyframe with timing and input state."""
    time: float
    x: float = 0.0
    y: float = 0.0
    buttons: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'time': round(self.time, 3),
            'x': round(self.x, 3),
            'y': round(self.y, 3),
            'buttons': self.buttons,
        }


class InputRecorder:
    """Records live joystick input to JSON scripts.

    Captures joystick axis positions and button states at a specified
    sample rate, outputting a script compatible with ScriptedInputHandler.
    """

    def __init__(
        self,
        duration: float,
        fps: int = 30,
        digital: bool = False,
        sparse: bool = False,
    ):
        """Initialize the recorder.

        Args:
            duration: Recording length in seconds
            fps: Sample rate (frames per second)
            digital: Quantize analog values to -1/0/1
            sparse: Only save keyframes when state changes
        """
        self.duration = duration
        self.fps = fps
        self.digital = digital
        self.sparse = sparse
        self.keyframes: List[RecordedKeyframe] = []
        self.input_handler: Optional[InputHandler] = None

        # State tracking for sparse mode
        self._last_x: Optional[float] = None
        self._last_y: Optional[float] = None
        self._last_buttons: Optional[List[int]] = None

    def _quantize(self, value: float) -> float:
        """Quantize analog value to digital (-1, 0, 1)."""
        if value > 0.5:
            return 1.0
        elif value < -0.5:
            return -1.0
        return 0.0

    def _get_pressed_buttons(self, button_dict: Dict[int, bool]) -> List[int]:
        """Convert button dict to list of pressed button IDs."""
        return sorted([btn_id for btn_id, pressed in button_dict.items() if pressed])

    def _state_changed(self, x: float, y: float, buttons: List[int]) -> bool:
        """Check if state has changed from last recorded keyframe."""
        if self._last_x is None:
            return True

        # Check axis change (with small threshold for noise)
        axis_threshold = 0.05 if not self.digital else 0.0
        if abs(x - self._last_x) > axis_threshold or abs(y - self._last_y) > axis_threshold:
            return True

        # Check button change
        if buttons != self._last_buttons:
            return True

        return False

    def _record_keyframe(self, current_time: float, x: float, y: float, buttons: List[int]):
        """Record a keyframe."""
        keyframe = RecordedKeyframe(
            time=current_time,
            x=x,
            y=y,
            buttons=buttons,
        )
        self.keyframes.append(keyframe)

        # Update state tracking
        self._last_x = x
        self._last_y = y
        self._last_buttons = buttons

    def record(self) -> List[RecordedKeyframe]:
        """Record joystick input for the configured duration.

        Returns:
            List of recorded keyframes
        """
        self.keyframes = []
        self._last_x = None
        self._last_y = None
        self._last_buttons = None

        # Initialize input handler
        self.input_handler = InputHandler()

        # Check joystick connection
        info = self.input_handler.verify_joystick()
        if not info['connected']:
            print("Warning: No joystick connected. Recording will be empty.", file=sys.stderr)
        else:
            print(f"Recording from: {info['name']}")
            print(f"  Axes: {info['axes']}, Buttons: {info['buttons']}")

        # Calculate frame timing
        frame_time = 1.0 / self.fps
        total_frames = int(self.duration * self.fps)

        print(f"\nRecording {self.duration}s at {self.fps}fps ({total_frames} frames)")
        print("Press Ctrl+C to stop early\n")

        # Countdown
        for i in range(3, 0, -1):
            print(f"Starting in {i}...", end='\r', flush=True)
            time.sleep(1)
        print("RECORDING!       ")

        start_time = time.time()

        try:
            for frame in range(total_frames):
                frame_start = time.time()
                current_time = frame * frame_time

                # Get joystick state
                x, y = self.input_handler.get_joystick_state()
                button_dict = self.input_handler.get_joystick_buttons()
                buttons = self._get_pressed_buttons(button_dict)

                # Apply digital quantization if enabled
                if self.digital:
                    x = self._quantize(x)
                    y = self._quantize(y)

                # Record keyframe (sparse mode: only on change)
                if not self.sparse or self._state_changed(x, y, buttons):
                    self._record_keyframe(current_time, x, y, buttons)

                # Display progress
                elapsed = time.time() - start_time
                remaining = self.duration - elapsed
                bar_width = 30
                progress = (frame + 1) / total_frames
                filled = int(bar_width * progress)
                bar = '#' * filled + '-' * (bar_width - filled)

                # Show current state
                btn_str = ','.join(map(str, buttons)) if buttons else '-'
                print(f"\rFrame {frame + 1:5d}/{total_frames} [{bar}] "
                      f"X:{x:+.2f} Y:{y:+.2f} BTN:[{btn_str}] "
                      f"Remaining: {remaining:.1f}s  ", end='', flush=True)

                # Sleep to maintain frame rate
                frame_elapsed = time.time() - frame_start
                sleep_time = frame_time - frame_elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nRecording stopped early.")
            # Trim duration to actual recorded time
            if self.keyframes:
                self.duration = self.keyframes[-1].time + frame_time

        finally:
            self.input_handler.cleanup()

        # Ensure we have at least start and end keyframes for sparse mode
        if self.sparse and len(self.keyframes) > 0:
            # Add final keyframe if not already there
            last_time = self.keyframes[-1].time
            if last_time < self.duration - frame_time:
                self._record_keyframe(
                    self.duration - frame_time,
                    self._last_x or 0.0,
                    self._last_y or 0.0,
                    self._last_buttons or []
                )

        print(f"\n\nRecording complete!")
        print(f"  Duration: {self.duration:.2f}s")
        print(f"  Keyframes: {len(self.keyframes)}")

        return self.keyframes

    def to_dict(self) -> dict:
        """Convert recording to dictionary for JSON export."""
        return {
            'name': 'Recorded Input',
            'description': f'Recorded at {self.fps}fps' +
                          (' (digital)' if self.digital else '') +
                          (' (sparse)' if self.sparse else ''),
            'duration': round(self.duration, 3),
            'fps': self.fps,
            'interpolation': 'step' if self.digital else 'smooth',
            'keyframes': [kf.to_dict() for kf in self.keyframes],
        }

    def save(self, path: str):
        """Save recording to JSON file.

        Args:
            path: Output file path
        """
        data = self.to_dict()

        # Ensure parent directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved to: {path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Record joystick input to JSON script for demo video export',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --duration 15 -o my-demo.json
  %(prog)s --duration 30 --fps 60 -o high-fps-demo.json
  %(prog)s --duration 10 --digital -o digital-input.json
  %(prog)s --duration 60 --sparse -o sparse-demo.json

The output JSON can be used with demo_video.py:
  python -m atari_style.core.demo_video joystick_test my-demo.json -o output.mp4
"""
    )

    parser.add_argument('--duration', '-d', type=float, required=True,
                        help='Recording duration in seconds')
    parser.add_argument('--fps', '-f', type=int, default=30,
                        help='Sample rate in frames per second (default: 30)')
    parser.add_argument('--digital', action='store_true',
                        help='Quantize analog values to -1/0/1 (for digital joysticks)')
    parser.add_argument('--sparse', '-s', action='store_true',
                        help='Only save keyframes when input state changes')
    parser.add_argument('-o', '--output', required=True,
                        help='Output JSON file path')

    args = parser.parse_args()

    # Validate arguments
    if args.duration <= 0:
        parser.error("Duration must be positive")
    if args.fps <= 0 or args.fps > 120:
        parser.error("FPS must be between 1 and 120")

    try:
        recorder = InputRecorder(
            duration=args.duration,
            fps=args.fps,
            digital=args.digital,
            sparse=args.sparse,
        )

        recorder.record()
        recorder.save(args.output)

    except KeyboardInterrupt:
        print("\nRecording cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
