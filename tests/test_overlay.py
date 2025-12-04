"""Tests for overlay system."""

import unittest
from unittest.mock import MagicMock

from atari_style.core.overlay import (
    OverlayManager,
    OverlayPosition,
    FrameOverlay,
    TimestampOverlay,
    FpsOverlay,
    DemoOverlay,
    OVERLAY_TYPES,
)


class TestOverlayPosition(unittest.TestCase):
    """Test OverlayPosition enum."""

    def test_from_string_full_names(self):
        """Test parsing full position names."""
        self.assertEqual(
            OverlayPosition.from_string('top-left'),
            OverlayPosition.TOP_LEFT
        )
        self.assertEqual(
            OverlayPosition.from_string('top-right'),
            OverlayPosition.TOP_RIGHT
        )
        self.assertEqual(
            OverlayPosition.from_string('bottom-left'),
            OverlayPosition.BOTTOM_LEFT
        )
        self.assertEqual(
            OverlayPosition.from_string('bottom-right'),
            OverlayPosition.BOTTOM_RIGHT
        )

    def test_from_string_abbreviations(self):
        """Test parsing abbreviated position names."""
        self.assertEqual(OverlayPosition.from_string('tl'), OverlayPosition.TOP_LEFT)
        self.assertEqual(OverlayPosition.from_string('tr'), OverlayPosition.TOP_RIGHT)
        self.assertEqual(OverlayPosition.from_string('bl'), OverlayPosition.BOTTOM_LEFT)
        self.assertEqual(OverlayPosition.from_string('br'), OverlayPosition.BOTTOM_RIGHT)

    def test_from_string_case_insensitive(self):
        """Test case insensitive parsing."""
        self.assertEqual(
            OverlayPosition.from_string('TOP-LEFT'),
            OverlayPosition.TOP_LEFT
        )
        self.assertEqual(
            OverlayPosition.from_string('Bottom-Right'),
            OverlayPosition.BOTTOM_RIGHT
        )

    def test_from_string_unknown_returns_default(self):
        """Test unknown position returns default."""
        self.assertEqual(
            OverlayPosition.from_string('unknown'),
            OverlayPosition.BOTTOM_LEFT
        )


class TestFrameOverlay(unittest.TestCase):
    """Test FrameOverlay formatting."""

    def test_format_basic(self):
        """Test basic frame formatting."""
        overlay = FrameOverlay()
        result = overlay.format(frame=150, total_frames=900)
        self.assertEqual(result, "Frame: 150/900")

    def test_format_first_frame(self):
        """Test first frame formatting."""
        overlay = FrameOverlay()
        result = overlay.format(frame=1, total_frames=100)
        self.assertEqual(result, "Frame: 1/100")

    def test_format_last_frame(self):
        """Test last frame formatting."""
        overlay = FrameOverlay()
        result = overlay.format(frame=100, total_frames=100)
        self.assertEqual(result, "Frame: 100/100")


class TestTimestampOverlay(unittest.TestCase):
    """Test TimestampOverlay formatting."""

    def test_format_zero(self):
        """Test timestamp at zero."""
        overlay = TimestampOverlay()
        result = overlay.format(frame=0, fps=30)
        self.assertEqual(result, "00:00.00")

    def test_format_seconds(self):
        """Test timestamp with seconds."""
        overlay = TimestampOverlay()
        result = overlay.format(frame=150, fps=30)  # 5 seconds
        self.assertEqual(result, "00:05.00")

    def test_format_minutes(self):
        """Test timestamp with minutes."""
        overlay = TimestampOverlay()
        result = overlay.format(frame=1800, fps=30)  # 60 seconds = 1 minute
        self.assertEqual(result, "01:00.00")

    def test_format_fractional_seconds(self):
        """Test timestamp with fractional seconds."""
        overlay = TimestampOverlay()
        result = overlay.format(frame=45, fps=30)  # 1.5 seconds
        self.assertEqual(result, "00:01.50")

    def test_format_complex_time(self):
        """Test timestamp with complex time."""
        overlay = TimestampOverlay()
        result = overlay.format(frame=3750, fps=30)  # 125 seconds = 2:05.00
        self.assertEqual(result, "02:05.00")


class TestFpsOverlay(unittest.TestCase):
    """Test FpsOverlay formatting."""

    def test_format_30fps(self):
        """Test 30 fps formatting."""
        overlay = FpsOverlay()
        result = overlay.format(fps=30)
        self.assertEqual(result, "30 fps")

    def test_format_60fps(self):
        """Test 60 fps formatting."""
        overlay = FpsOverlay()
        result = overlay.format(fps=60)
        self.assertEqual(result, "60 fps")


class TestDemoOverlay(unittest.TestCase):
    """Test DemoOverlay formatting."""

    def test_format_with_name(self):
        """Test formatting with demo name."""
        overlay = DemoOverlay()
        result = overlay.format(demo_name='starfield')
        self.assertEqual(result, "starfield")

    def test_format_empty_name(self):
        """Test formatting with empty name returns default."""
        overlay = DemoOverlay()
        result = overlay.format(demo_name='')
        self.assertEqual(result, "Demo")


class TestOverlayManager(unittest.TestCase):
    """Test OverlayManager class."""

    def test_add_single_overlay(self):
        """Test adding a single overlay."""
        manager = OverlayManager()
        manager.add('frame')
        self.assertEqual(len(manager), 1)

    def test_add_multiple_overlays(self):
        """Test adding multiple overlays."""
        manager = OverlayManager()
        manager.add('frame').add('timestamp').add('fps')
        self.assertEqual(len(manager), 3)

    def test_add_unknown_overlay_raises(self):
        """Test adding unknown overlay type raises."""
        manager = OverlayManager()
        with self.assertRaises(ValueError) as ctx:
            manager.add('unknown')
        self.assertIn('unknown', str(ctx.exception))
        self.assertIn('Available', str(ctx.exception))

    def test_add_with_position(self):
        """Test adding overlay with custom position."""
        manager = OverlayManager()
        manager.add('frame', position=OverlayPosition.TOP_LEFT)
        self.assertEqual(manager.overlays[0].position, OverlayPosition.TOP_LEFT)

    def test_add_with_color(self):
        """Test adding overlay with custom color."""
        manager = OverlayManager()
        manager.add('frame', color='bright_cyan')
        self.assertEqual(manager.overlays[0].color, 'bright_cyan')

    def test_add_from_string(self):
        """Test adding overlays from comma-separated string."""
        manager = OverlayManager()
        manager.add_from_string('frame,timestamp,fps')
        self.assertEqual(len(manager), 3)

    def test_add_from_string_with_spaces(self):
        """Test adding overlays with spaces in string."""
        manager = OverlayManager()
        manager.add_from_string('frame, timestamp, fps')
        self.assertEqual(len(manager), 3)

    def test_add_from_string_with_position(self):
        """Test adding overlays from string with position."""
        manager = OverlayManager()
        manager.add_from_string('frame', position='top-left')
        self.assertEqual(manager.overlays[0].position, OverlayPosition.TOP_LEFT)

    def test_clear(self):
        """Test clearing all overlays."""
        manager = OverlayManager()
        manager.add('frame').add('timestamp')
        self.assertEqual(len(manager), 2)
        manager.clear()
        self.assertEqual(len(manager), 0)

    def test_bool_empty(self):
        """Test bool with no overlays."""
        manager = OverlayManager()
        self.assertFalse(manager)

    def test_bool_with_overlays(self):
        """Test bool with overlays."""
        manager = OverlayManager()
        manager.add('frame')
        self.assertTrue(manager)

    def test_render_calls_draw_text(self):
        """Test that render calls draw_text on renderer."""
        manager = OverlayManager()
        manager.add('frame')

        # Mock renderer
        mock_renderer = MagicMock()
        mock_renderer.width = 100
        mock_renderer.height = 40

        manager.render(
            mock_renderer,
            frame=50,
            total_frames=100,
            fps=30,
            demo_name='test',
        )

        # Verify draw_text was called
        mock_renderer.draw_text.assert_called()

    def test_overlay_types_registered(self):
        """Test all overlay types are registered."""
        expected = {'frame', 'timestamp', 'fps', 'demo'}
        self.assertEqual(set(OVERLAY_TYPES.keys()), expected)


class TestOverlayPositioning(unittest.TestCase):
    """Test overlay positioning calculations."""

    def test_top_left_position(self):
        """Test top-left position calculation."""
        overlay = FrameOverlay(position=OverlayPosition.TOP_LEFT)

        mock_renderer = MagicMock()
        mock_renderer.width = 100
        mock_renderer.height = 40

        x, y = overlay._calculate_position(mock_renderer, "Frame: 1/100")

        self.assertEqual(x, 1)  # padding
        self.assertEqual(y, 1)  # padding

    def test_bottom_right_position(self):
        """Test bottom-right position calculation."""
        overlay = FrameOverlay(position=OverlayPosition.BOTTOM_RIGHT)

        mock_renderer = MagicMock()
        mock_renderer.width = 100
        mock_renderer.height = 40

        text = "Frame: 1/100"
        x, y = overlay._calculate_position(mock_renderer, text)

        self.assertEqual(x, 100 - len(text) - 1)  # width - text_len - padding
        self.assertEqual(y, 40 - 1 - 1)  # height - 1 - padding


if __name__ == '__main__':
    unittest.main()
