"""Overlay system for video exports.

Provides frame counters, timestamps, and other metadata overlays
for demo video exports. Overlays are rendered as terminal characters
directly in the buffer.

Usage:
    from atari_style.core.overlay import OverlayManager, OverlayPosition

    manager = OverlayManager()
    manager.add('frame', position=OverlayPosition.BOTTOM_LEFT)
    manager.add('timestamp', position=OverlayPosition.BOTTOM_RIGHT)

    # In render loop:
    manager.render(renderer, frame=150, total_frames=900, fps=30, demo_name='starfield')
"""

from enum import Enum
from typing import List, Optional, Protocol, Tuple


class OverlayPosition(Enum):
    """Position for overlay rendering."""
    TOP_LEFT = 'top-left'
    TOP_RIGHT = 'top-right'
    BOTTOM_LEFT = 'bottom-left'
    BOTTOM_RIGHT = 'bottom-right'

    @classmethod
    def from_string(cls, s: str) -> 'OverlayPosition':
        """Parse position from string."""
        mapping = {
            'top-left': cls.TOP_LEFT,
            'top-right': cls.TOP_RIGHT,
            'bottom-left': cls.BOTTOM_LEFT,
            'bottom-right': cls.BOTTOM_RIGHT,
            'tl': cls.TOP_LEFT,
            'tr': cls.TOP_RIGHT,
            'bl': cls.BOTTOM_LEFT,
            'br': cls.BOTTOM_RIGHT,
        }
        return mapping.get(s.lower(), cls.BOTTOM_LEFT)


class RendererProtocol(Protocol):
    """Protocol for renderer compatibility."""
    width: int
    height: int

    def draw_text(self, x: int, y: int, text: str, color: Optional[str] = None) -> None:
        """Draw text at position."""
        ...


class Overlay:
    """Base class for overlay types."""

    def __init__(self, position: OverlayPosition = OverlayPosition.BOTTOM_LEFT):
        self.position = position
        self.color = 'yellow'  # Default overlay color
        self.padding = 1  # Padding from edge

    def format(self, **kwargs) -> str:
        """Format the overlay text. Override in subclasses."""
        raise NotImplementedError

    def render(self, renderer: RendererProtocol, **kwargs) -> None:
        """Render the overlay to the buffer."""
        text = self.format(**kwargs)
        x, y = self._calculate_position(renderer, text)
        renderer.draw_text(x, y, text, self.color)

    def _calculate_position(self, renderer: RendererProtocol, text: str) -> Tuple[int, int]:
        """Calculate x, y position based on position setting."""
        text_len = len(text)

        if self.position == OverlayPosition.TOP_LEFT:
            return (self.padding, self.padding)
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (renderer.width - text_len - self.padding, self.padding)
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (self.padding, renderer.height - 1 - self.padding)
        else:  # BOTTOM_RIGHT
            return (renderer.width - text_len - self.padding, renderer.height - 1 - self.padding)


class FrameOverlay(Overlay):
    """Frame counter overlay (e.g., "Frame: 150/900")."""

    def format(self, frame: int = 0, total_frames: int = 0, **kwargs) -> str:
        """Format frame counter."""
        return f"Frame: {frame}/{total_frames}"


class TimestampOverlay(Overlay):
    """Timestamp overlay (e.g., "00:05.00")."""

    def format(self, frame: int = 0, fps: int = 30, **kwargs) -> str:
        """Format timestamp from frame number."""
        total_seconds = frame / fps if fps > 0 else 0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"


class FpsOverlay(Overlay):
    """FPS indicator overlay (e.g., "30 fps")."""

    def format(self, fps: int = 30, **kwargs) -> str:
        """Format FPS indicator."""
        return f"{fps} fps"


class DemoOverlay(Overlay):
    """Demo name overlay."""

    def format(self, demo_name: str = '', **kwargs) -> str:
        """Format demo name."""
        return demo_name if demo_name else 'Demo'


# Registry of overlay types
OVERLAY_TYPES = {
    'frame': FrameOverlay,
    'timestamp': TimestampOverlay,
    'fps': FpsOverlay,
    'demo': DemoOverlay,
}


class OverlayManager:
    """Manages multiple overlays for video export.

    Handles positioning to avoid overlaps and provides a simple API
    for adding and rendering overlays.
    """

    # Default positions for each overlay type when not specified
    DEFAULT_POSITIONS = {
        'frame': OverlayPosition.BOTTOM_LEFT,
        'timestamp': OverlayPosition.BOTTOM_RIGHT,
        'fps': OverlayPosition.TOP_RIGHT,
        'demo': OverlayPosition.TOP_LEFT,
    }

    def __init__(self):
        self.overlays: List[Overlay] = []
        self._position_offsets: dict = {
            OverlayPosition.TOP_LEFT: 0,
            OverlayPosition.TOP_RIGHT: 0,
            OverlayPosition.BOTTOM_LEFT: 0,
            OverlayPosition.BOTTOM_RIGHT: 0,
        }

    def add(
        self,
        overlay_type: str,
        position: Optional[OverlayPosition] = None,
        color: Optional[str] = None,
    ) -> 'OverlayManager':
        """Add an overlay by type name.

        Args:
            overlay_type: One of 'frame', 'timestamp', 'fps', 'demo'
            position: Override default position
            color: Override default color

        Returns:
            Self for chaining
        """
        if overlay_type not in OVERLAY_TYPES:
            available = ', '.join(OVERLAY_TYPES.keys())
            raise ValueError(f"Unknown overlay type '{overlay_type}'. Available: {available}")

        # Use default position if not specified
        if position is None:
            position = self.DEFAULT_POSITIONS.get(overlay_type, OverlayPosition.BOTTOM_LEFT)

        overlay_class = OVERLAY_TYPES[overlay_type]
        overlay = overlay_class(position=position)

        if color:
            overlay.color = color

        # Adjust padding to avoid overlaps at same position
        offset = self._position_offsets[position]
        if position in (OverlayPosition.TOP_LEFT, OverlayPosition.TOP_RIGHT):
            overlay.padding = 1 + offset
        else:
            overlay.padding = 1 + offset

        self._position_offsets[position] += 1

        self.overlays.append(overlay)
        return self

    def add_from_string(self, overlay_spec: str, position: Optional[str] = None) -> 'OverlayManager':
        """Add overlays from comma-separated string.

        Args:
            overlay_spec: Comma-separated overlay types (e.g., "frame,timestamp")
            position: Position for all overlays (or use defaults)

        Returns:
            Self for chaining
        """
        pos = OverlayPosition.from_string(position) if position else None

        for overlay_type in overlay_spec.split(','):
            overlay_type = overlay_type.strip()
            if overlay_type:
                self.add(overlay_type, position=pos)

        return self

    def render(
        self,
        renderer: RendererProtocol,
        frame: int = 0,
        total_frames: int = 0,
        fps: int = 30,
        demo_name: str = '',
    ) -> None:
        """Render all overlays to the buffer.

        Args:
            renderer: Renderer with draw_text method
            frame: Current frame number (1-indexed for display)
            total_frames: Total frames in video
            fps: Frames per second
            demo_name: Name of the demo
        """
        for overlay in self.overlays:
            overlay.render(
                renderer,
                frame=frame,
                total_frames=total_frames,
                fps=fps,
                demo_name=demo_name,
            )

    def clear(self) -> None:
        """Remove all overlays."""
        self.overlays.clear()
        for pos in self._position_offsets:
            self._position_offsets[pos] = 0

    def __len__(self) -> int:
        """Return number of active overlays."""
        return len(self.overlays)

    def __bool__(self) -> bool:
        """Return True if any overlays are configured."""
        return len(self.overlays) > 0
