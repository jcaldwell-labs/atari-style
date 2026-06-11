"""Attract mode system for recording and playing back game demos.

Provides functionality for games to record demo gameplay and play it back
in the menu as an "attract mode" preview, similar to arcade cabinets.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum


class DemoEventType(Enum):
    """Types of events that can be recorded in a demo."""
    INPUT = "input"  # Input event (direction, button press)
    STATE = "state"  # Game state snapshot
    FRAME = "frame"  # Frame boundary marker


class DemoRecorder:
    """Records game demo sessions for playback."""

    def __init__(self, game_name: str):
        """Initialize demo recorder.

        Args:
            game_name: Name of the game being recorded
        """
        self.game_name = game_name
        self.recording = False
        self.events: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None

    def start_recording(self):
        """Start recording a demo."""
        self.recording = True
        self.events = []
        self.start_time = time.time()

    def stop_recording(self):
        """Stop recording the demo."""
        self.recording = False

    def record_input(self, input_type: str, value: Any = None):
        """Record an input event.

        Args:
            input_type: Type of input (e.g., "up", "down", "button_a")
            value: Optional value (e.g., axis position, button state)
        """
        if not self.recording:
            return

        timestamp = time.time() - self.start_time
        self.events.append({
            "type": DemoEventType.INPUT.value,
            "timestamp": timestamp,
            "input_type": input_type,
            "value": value,
        })

    def record_state(self, state_data: Dict[str, Any]):
        """Record a game state snapshot.

        Args:
            state_data: Dictionary containing game state information
        """
        if not self.recording:
            return

        timestamp = time.time() - self.start_time
        self.events.append({
            "type": DemoEventType.STATE.value,
            "timestamp": timestamp,
            "state": state_data,
        })

    def record_frame(self, frame_number: int):
        """Record a frame marker.

        Args:
            frame_number: Current frame number
        """
        if not self.recording:
            return

        timestamp = time.time() - self.start_time
        self.events.append({
            "type": DemoEventType.FRAME.value,
            "timestamp": timestamp,
            "frame": frame_number,
        })

    def save(self, filepath: Path):
        """Save recorded demo to file.

        Args:
            filepath: Path to save the demo file
        """
        demo_data = {
            "game": self.game_name,
            "duration": time.time() - self.start_time if self.start_time else 0,
            "events": self.events,
            "version": "1.0",
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(demo_data, f, indent=2)


class DemoPlayer:
    """Plays back recorded game demos."""

    def __init__(self, filepath: Path):
        """Initialize demo player.

        Args:
            filepath: Path to the demo file
        """
        self.filepath = filepath
        self.events: List[Dict[str, Any]] = []
        self.duration: float = 0
        self.current_event_index = 0
        self.playback_start_time: Optional[float] = None
        self.playing = False

        self._load_demo()

    def _load_demo(self):
        """Load demo data from file."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"Demo file not found: {self.filepath}")

        with open(self.filepath, 'r') as f:
            demo_data = json.load(f)

        self.events = demo_data.get("events", [])
        self.duration = demo_data.get("duration", 0)

    def start_playback(self):
        """Start playing back the demo."""
        self.playing = True
        self.current_event_index = 0
        self.playback_start_time = time.time()

    def stop_playback(self):
        """Stop playback."""
        self.playing = False

    def get_current_events(self) -> List[Dict[str, Any]]:
        """Get all events that should occur at the current playback time.

        Returns:
            List of event dictionaries that should be processed now
        """
        if not self.playing or self.playback_start_time is None:
            return []

        current_time = time.time() - self.playback_start_time
        events_to_process = []

        while self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            if event["timestamp"] <= current_time:
                events_to_process.append(event)
                self.current_event_index += 1
            else:
                break

        return events_to_process

    def is_finished(self) -> bool:
        """Check if playback has finished.

        Returns:
            True if all events have been played
        """
        return self.current_event_index >= len(self.events)

    def loop(self):
        """Loop playback from the beginning."""
        self.current_event_index = 0
        self.playback_start_time = time.time()


class AttractModeManager:
    """Manages attract mode demos for the menu system."""

    def __init__(self, demos_dir: Path):
        """Initialize attract mode manager.

        Args:
            demos_dir: Directory containing demo files
        """
        self.demos_dir = demos_dir
        self.demos_dir.mkdir(parents=True, exist_ok=True)
        self.available_demos: Dict[str, Path] = {}
        self._scan_demos()

    def _scan_demos(self):
        """Scan demos directory for available demo files."""
        self.available_demos = {}
        for demo_file in self.demos_dir.glob("*.json"):
            game_name = demo_file.stem
            self.available_demos[game_name] = demo_file

    def get_demo_player(self, game_name: str) -> Optional[DemoPlayer]:
        """Get a demo player for a specific game.

        Args:
            game_name: Name of the game

        Returns:
            DemoPlayer instance or None if no demo exists
        """
        if game_name not in self.available_demos:
            return None

        try:
            return DemoPlayer(self.available_demos[game_name])
        except Exception as e:
            print(f"Failed to load demo for {game_name}: {e}")
            return None

    def has_demo(self, game_name: str) -> bool:
        """Check if a demo exists for a game.

        Args:
            game_name: Name of the game

        Returns:
            True if a demo file exists
        """
        return game_name in self.available_demos

    def list_demos(self) -> List[str]:
        """Get list of games with available demos.

        Returns:
            List of game names with demos
        """
        return list(self.available_demos.keys())


def create_simple_demo(game_name: str, demo_path: Path, duration: float = 30.0):
    """Helper function to create a simple placeholder demo.

    This can be used by games that don't yet have recorded demos but want
    to show something in attract mode.

    Args:
        game_name: Name of the game
        demo_path: Path to save the demo
        duration: Duration of the demo in seconds
    """
    recorder = DemoRecorder(game_name)
    recorder.start_recording()

    # Create some simple movement events for demo purposes
    moves = ["up", "down", "left", "right", "select"]
    for i in range(int(duration / 2)):
        # Simulate input every 2 seconds
        time.sleep(2)
        move = moves[i % len(moves)]
        recorder.record_input(move)

    recorder.stop_recording()
    recorder.save(demo_path)
