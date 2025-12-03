"""Scripted input handler for demo video generation.

Provides a mock InputHandler that replays timed input sequences from
a script file, enabling reproducible demo videos without hardware.

Usage:
    from atari_style.core.scripted_input import ScriptedInputHandler

    # Load and use scripted input
    handler = ScriptedInputHandler('scripts/demos/joystick-demo.json')
    handler.start()

    while handler.is_active():
        x, y = handler.get_joystick_state()
        buttons = handler.get_joystick_buttons()
        # ... render frame ...
        handler.advance_frame(1/30)  # Advance by frame time
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InputKeyframe:
    """A single keyframe in an input script."""
    time: float
    x: float = 0.0
    y: float = 0.0
    buttons: List[int] = field(default_factory=list)


@dataclass
class InputScript:
    """Parsed input script with metadata and keyframes."""
    duration: float
    fps: int
    keyframes: List[InputKeyframe]
    interpolation: str = "smooth"  # "smooth", "linear", or "step"
    name: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputScript':
        """Create InputScript from dictionary (JSON data)."""
        keyframes = [
            InputKeyframe(
                time=kf['time'],
                x=kf.get('x', 0.0),
                y=kf.get('y', 0.0),
                buttons=kf.get('buttons', [])
            )
            for kf in data.get('keyframes', [])
        ]

        return cls(
            duration=data.get('duration', 10.0),
            fps=data.get('fps', 30),
            keyframes=sorted(keyframes, key=lambda k: k.time),
            interpolation=data.get('interpolation', 'smooth'),
            name=data.get('name', ''),
            description=data.get('description', '')
        )

    @classmethod
    def from_file(cls, path: str) -> 'InputScript':
        """Load InputScript from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def _smooth_interpolate(t: float) -> float:
    """Smooth step interpolation (ease-in-out)."""
    # Hermite interpolation: 3t² - 2t³
    return t * t * (3 - 2 * t)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


class ScriptedInputHandler:
    """Mock InputHandler that replays scripted input sequences.

    Designed to be a drop-in replacement for InputHandler in demo contexts,
    providing the same interface for joystick state queries.
    """

    def __init__(self, script_path: Optional[str] = None, script: Optional[InputScript] = None):
        """Initialize with script file or InputScript object.

        Args:
            script_path: Path to JSON script file
            script: Pre-loaded InputScript object
        """
        if script:
            self.script = script
        elif script_path:
            self.script = InputScript.from_file(script_path)
        else:
            raise ValueError("Must provide either script_path or script")

        self.current_time = 0.0
        self.started = False
        self._start_wall_time = 0.0

        # For InputHandler interface compatibility
        self.joystick_initialized = True  # Pretend joystick exists
        self.term = None  # Will be set if needed

    def start(self):
        """Start the script playback."""
        self.current_time = 0.0
        self.started = True
        self._start_wall_time = time.time()

    def reset(self):
        """Reset script to beginning."""
        self.current_time = 0.0
        self.started = False

    def is_active(self) -> bool:
        """Check if script is still playing (not past duration)."""
        return self.started and self.current_time < self.script.duration

    def advance_frame(self, dt: float):
        """Advance script time by dt seconds."""
        self.current_time += dt

    def advance_to_wall_time(self):
        """Advance script time to match wall clock (for real-time playback)."""
        if self.started:
            self.current_time = time.time() - self._start_wall_time

    def get_frame_count(self) -> int:
        """Get total number of frames in script."""
        return int(self.script.duration * self.script.fps)

    def get_current_frame(self) -> int:
        """Get current frame number."""
        return int(self.current_time * self.script.fps)

    def _find_keyframes(self, t: float) -> Tuple[Optional[InputKeyframe], Optional[InputKeyframe], float]:
        """Find surrounding keyframes and interpolation factor for time t.

        Returns:
            (prev_keyframe, next_keyframe, interpolation_t)
        """
        if not self.script.keyframes:
            return None, None, 0.0

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for i, kf in enumerate(self.script.keyframes):
            if kf.time <= t:
                prev_kf = kf
            if kf.time > t and next_kf is None:
                next_kf = kf
                break

        # Handle edge cases
        if prev_kf is None:
            prev_kf = self.script.keyframes[0]
        if next_kf is None:
            next_kf = prev_kf  # Stay at last keyframe
            return prev_kf, next_kf, 1.0

        # Calculate interpolation factor
        if next_kf.time == prev_kf.time:
            interp_t = 1.0
        else:
            interp_t = (t - prev_kf.time) / (next_kf.time - prev_kf.time)
            interp_t = max(0.0, min(1.0, interp_t))

        return prev_kf, next_kf, interp_t

    def _interpolate_position(self, prev_kf: InputKeyframe, next_kf: InputKeyframe, t: float) -> Tuple[float, float]:
        """Interpolate position between keyframes."""
        if self.script.interpolation == "step":
            return prev_kf.x, prev_kf.y
        elif self.script.interpolation == "smooth":
            t = _smooth_interpolate(t)
        # Linear or smoothed linear
        x = _lerp(prev_kf.x, next_kf.x, t)
        y = _lerp(prev_kf.y, next_kf.y, t)
        return x, y

    def get_joystick_state(self) -> Tuple[float, float]:
        """Get interpolated joystick position at current time.

        Returns:
            (x, y) tuple with values in range -1.0 to 1.0
        """
        prev_kf, next_kf, t = self._find_keyframes(self.current_time)

        if prev_kf is None:
            return 0.0, 0.0

        return self._interpolate_position(prev_kf, next_kf, t)

    def get_joystick_buttons(self) -> Dict[int, bool]:
        """Get button states at current time.

        Buttons use the previous keyframe's state (no interpolation).

        Returns:
            Dictionary mapping button IDs to pressed state
        """
        prev_kf, _, _ = self._find_keyframes(self.current_time)

        if prev_kf is None:
            return {}

        # Return dict with True for pressed buttons, False for others (up to 12 buttons)
        return {i: (i in prev_kf.buttons) for i in range(12)}

    def verify_joystick(self) -> Dict[str, Any]:
        """Return mock joystick info (for interface compatibility)."""
        return {
            'connected': True,
            'name': f'Scripted: {self.script.name or "Demo"}',
            'axes': 2,
            'buttons': 12,
        }

    def get_input(self, timeout: float = 0.1):
        """Mock get_input for interface compatibility.

        In scripted mode, this doesn't block - just returns NONE.
        """
        from .input_handler import InputType
        return InputType.NONE

    def cleanup(self):
        """No-op cleanup for interface compatibility."""
        pass


def create_simple_script(
    duration: float,
    movements: List[Tuple[float, float, float, List[int]]],
    fps: int = 30,
    interpolation: str = "smooth"
) -> InputScript:
    """Helper to create scripts programmatically.

    Args:
        duration: Total duration in seconds
        movements: List of (time, x, y, buttons) tuples
        fps: Frames per second
        interpolation: "smooth", "linear", or "step"

    Returns:
        InputScript object
    """
    keyframes = [
        InputKeyframe(time=t, x=x, y=y, buttons=btns)
        for t, x, y, btns in movements
    ]

    return InputScript(
        duration=duration,
        fps=fps,
        keyframes=keyframes,
        interpolation=interpolation
    )
