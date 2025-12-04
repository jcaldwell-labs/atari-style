"""Video scripting framework for declarative video generation.

Provides a JSON-based scripting language for defining educational and
demonstration videos with segments, transitions, and parameter sweeps.

Usage:
    from atari_style.core.video_script import VideoScript

    # Load script from JSON file
    script = VideoScript.from_file('scripts/videos/lissajous-intro.json')

    # Execute script to generate video
    script.render('output.mp4')

Example script format:
    {
        "name": "lissajous-educational",
        "version": "1.0",
        "format": "youtube_landscape",
        "segments": [
            {"type": "title", "duration": 3.0, "text": "Understanding Lissajous"},
            {"type": "visualization", "visualizer": "lissajous", "duration": 10.0, "params": {...}}
        ]
    }
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

from .video_base import VideoFormat


class SegmentType(Enum):
    """Types of segments in a video script."""
    TITLE = "title"
    VISUALIZATION = "visualization"
    SWEEP = "sweep"
    TRANSITION = "transition"
    PAUSE = "pause"


class EasingType(Enum):
    """Easing functions for parameter transitions."""
    LINEAR = "linear"
    SMOOTH = "smooth"  # Smoothstep
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


# Format presets matching video_base.py patterns
FORMAT_PRESETS: Dict[str, VideoFormat] = {
    "preview": VideoFormat("preview", 1280, 720, 15, description="Quick preview"),
    "youtube_landscape": VideoFormat("youtube_landscape", 1920, 1080, 30, description="YouTube 16:9"),
    "youtube_shorts": VideoFormat("youtube_shorts", 1080, 1920, 30, max_duration=60, description="YouTube Shorts"),
    "4k": VideoFormat("4k", 3840, 2160, 30, description="4K UHD"),
    "instagram_square": VideoFormat("instagram_square", 1080, 1080, 30, description="Instagram square"),
    "twitter": VideoFormat("twitter", 1280, 720, 30, max_duration=140, description="Twitter/X video"),
}


@dataclass
class TransitionConfig:
    """Configuration for parameter transitions."""
    easing: EasingType = EasingType.SMOOTH
    duration: float = 1.0  # Transition duration in seconds

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransitionConfig':
        easing = EasingType(data.get('easing', 'smooth'))
        duration = float(data.get('duration', 1.0))
        return cls(easing=easing, duration=duration)


@dataclass
class Segment(ABC):
    """Base class for video segments."""
    duration: float

    @abstractmethod
    def get_type(self) -> SegmentType:
        """Return the segment type."""
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Segment':
        """Factory method to create appropriate segment type."""
        segment_type = data.get('type', 'visualization')

        if segment_type == 'title':
            return TitleSegment.from_dict(data)
        elif segment_type == 'visualization':
            return VisualizationSegment.from_dict(data)
        elif segment_type == 'sweep':
            return SweepSegment.from_dict(data)
        elif segment_type == 'transition':
            return TransitionSegment.from_dict(data)
        elif segment_type == 'pause':
            return PauseSegment.from_dict(data)
        else:
            raise ValueError(f"Unknown segment type: {segment_type}")


@dataclass
class TitleSegment(Segment):
    """Title card segment with text overlay."""
    text: str
    subtitle: str = ""
    background_color: str = "black"
    text_color: str = "white"
    font_size: int = 48

    def get_type(self) -> SegmentType:
        return SegmentType.TITLE

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TitleSegment':
        return cls(
            duration=float(data.get('duration', 3.0)),
            text=data.get('text', ''),
            subtitle=data.get('subtitle', ''),
            background_color=data.get('background_color', 'black'),
            text_color=data.get('text_color', 'white'),
            font_size=int(data.get('font_size', 48))
        )


@dataclass
class VisualizationSegment(Segment):
    """Segment showing a visualizer with fixed parameters."""
    visualizer: str
    params: Dict[str, float] = field(default_factory=dict)
    color_mode: int = 0
    transition_in: Optional[TransitionConfig] = None
    transition_out: Optional[TransitionConfig] = None

    def get_type(self) -> SegmentType:
        return SegmentType.VISUALIZATION

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualizationSegment':
        transition_in = None
        transition_out = None

        if 'transition_in' in data:
            transition_in = TransitionConfig.from_dict(data['transition_in'])
        if 'transition_out' in data:
            transition_out = TransitionConfig.from_dict(data['transition_out'])

        return cls(
            duration=float(data.get('duration', 10.0)),
            visualizer=data.get('visualizer', ''),
            params=data.get('params', {}),
            color_mode=int(data.get('color_mode', 0)),
            transition_in=transition_in,
            transition_out=transition_out
        )


@dataclass
class SweepSegment(Segment):
    """Segment that sweeps parameters from one value to another."""
    visualizer: str
    from_params: Dict[str, float]
    to_params: Dict[str, float]
    easing: EasingType = EasingType.SMOOTH
    color_mode: int = 0

    def get_type(self) -> SegmentType:
        return SegmentType.SWEEP

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SweepSegment':
        return cls(
            duration=float(data.get('duration', 10.0)),
            visualizer=data.get('visualizer', ''),
            from_params=data.get('from', {}),
            to_params=data.get('to', {}),
            easing=EasingType(data.get('easing', 'smooth')),
            color_mode=int(data.get('color_mode', 0))
        )


@dataclass
class TransitionSegment(Segment):
    """Visual transition between segments (fade, wipe, etc.)."""
    effect: str = "fade"  # fade, wipe, dissolve

    def get_type(self) -> SegmentType:
        return SegmentType.TRANSITION

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransitionSegment':
        return cls(
            duration=float(data.get('duration', 1.0)),
            effect=data.get('effect', 'fade')
        )


@dataclass
class PauseSegment(Segment):
    """Hold the previous frame for a duration."""

    def get_type(self) -> SegmentType:
        return SegmentType.PAUSE

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PauseSegment':
        return cls(duration=float(data.get('duration', 2.0)))


@dataclass
class VideoScript:
    """Complete video script definition."""
    name: str
    segments: List[Segment]
    format: VideoFormat = field(default_factory=lambda: FORMAT_PRESETS['youtube_landscape'])
    version: str = "1.0"
    description: str = ""
    author: str = ""

    @property
    def total_duration(self) -> float:
        """Calculate total video duration from all segments."""
        return sum(seg.duration for seg in self.segments)

    @property
    def segment_count(self) -> int:
        """Number of segments in the script."""
        return len(self.segments)

    def validate(self) -> List[str]:
        """Validate the script and return list of errors."""
        errors = []

        if not self.name:
            errors.append("Script name is required")

        if not self.segments:
            errors.append("Script must have at least one segment")

        # Check format duration limits
        if self.format.max_duration and self.total_duration > self.format.max_duration:
            errors.append(
                f"Total duration ({self.total_duration:.1f}s) exceeds format limit "
                f"({self.format.max_duration}s for {self.format.name})"
            )

        # Validate each segment
        for i, segment in enumerate(self.segments):
            if segment.duration <= 0:
                errors.append(f"Segment {i}: duration must be positive")

            if isinstance(segment, (VisualizationSegment, SweepSegment)):
                if not segment.visualizer:
                    errors.append(f"Segment {i}: visualizer is required")

        return errors

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoScript':
        """Create VideoScript from dictionary (JSON data)."""
        # Parse format
        format_name = data.get('format', 'youtube_landscape')
        if isinstance(format_name, str):
            video_format = FORMAT_PRESETS.get(format_name, FORMAT_PRESETS['youtube_landscape'])
        else:
            # Custom format dict
            video_format = VideoFormat(
                name=format_name.get('name', 'custom'),
                width=format_name.get('width', 1920),
                height=format_name.get('height', 1080),
                fps=format_name.get('fps', 30),
                max_duration=format_name.get('max_duration'),
                description=format_name.get('description', '')
            )

        # Parse segments
        segments = [
            Segment.from_dict(seg_data)
            for seg_data in data.get('segments', [])
        ]

        return cls(
            name=data.get('name', 'untitled'),
            segments=segments,
            format=video_format,
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            author=data.get('author', '')
        )

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'VideoScript':
        """Load VideoScript from JSON file."""
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        def segment_to_dict(seg: Segment) -> Dict[str, Any]:
            result = {'type': seg.get_type().value, 'duration': seg.duration}

            if isinstance(seg, TitleSegment):
                result.update({
                    'text': seg.text,
                    'subtitle': seg.subtitle,
                    'background_color': seg.background_color,
                    'text_color': seg.text_color,
                    'font_size': seg.font_size
                })
            elif isinstance(seg, VisualizationSegment):
                result.update({
                    'visualizer': seg.visualizer,
                    'params': seg.params,
                    'color_mode': seg.color_mode
                })
            elif isinstance(seg, SweepSegment):
                result.update({
                    'visualizer': seg.visualizer,
                    'from': seg.from_params,
                    'to': seg.to_params,
                    'easing': seg.easing.value,
                    'color_mode': seg.color_mode
                })
            elif isinstance(seg, TransitionSegment):
                result['effect'] = seg.effect

            return result

        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'format': self.format.name,
            'segments': [segment_to_dict(seg) for seg in self.segments]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Union[str, Path]) -> None:
        """Save script to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
