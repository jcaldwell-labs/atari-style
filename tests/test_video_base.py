#!/usr/bin/env python3
"""Tests for unified video export base infrastructure.

Tests the shared components in atari_style/core/video_base.py:
- VideoFormat dataclass
- FFmpegEncoder
- ProgressReporter
- PresetManager
- VideoExporter base class
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from atari_style.core.video_base import (
    VideoFormat,
    FFmpegEncoder,
    ProgressReporter,
    PresetManager,
    VideoExporter,
)


class TestVideoFormat(unittest.TestCase):
    """Test VideoFormat dataclass."""

    def test_aspect_ratio_16_9(self):
        """Test aspect ratio calculation for 16:9."""
        fmt = VideoFormat("test", 1920, 1080, 30)
        self.assertEqual(fmt.aspect_ratio, "16:9")

    def test_aspect_ratio_9_16(self):
        """Test aspect ratio calculation for 9:16 (vertical)."""
        fmt = VideoFormat("test", 1080, 1920, 30)
        self.assertEqual(fmt.aspect_ratio, "9:16")

    def test_aspect_ratio_1_1(self):
        """Test aspect ratio calculation for 1:1 (square)."""
        fmt = VideoFormat("test", 1080, 1080, 30)
        self.assertEqual(fmt.aspect_ratio, "1:1")

    def test_is_vertical_true(self):
        """Test vertical format detection."""
        fmt = VideoFormat("test", 1080, 1920, 30)
        self.assertTrue(fmt.is_vertical)

    def test_is_vertical_false(self):
        """Test horizontal format detection."""
        fmt = VideoFormat("test", 1920, 1080, 30)
        self.assertFalse(fmt.is_vertical)

    def test_is_square_true(self):
        """Test square format detection."""
        fmt = VideoFormat("test", 1080, 1080, 30)
        self.assertTrue(fmt.is_square)

    def test_is_square_false(self):
        """Test non-square format detection."""
        fmt = VideoFormat("test", 1920, 1080, 30)
        self.assertFalse(fmt.is_square)

    def test_default_crf(self):
        """Test default CRF value."""
        fmt = VideoFormat("test", 1920, 1080, 30)
        self.assertEqual(fmt.crf, 23)

    def test_custom_crf(self):
        """Test custom CRF value."""
        fmt = VideoFormat("test", 1920, 1080, 30, crf=18)
        self.assertEqual(fmt.crf, 18)


class TestFFmpegEncoder(unittest.TestCase):
    """Test FFmpegEncoder."""

    def setUp(self):
        """Set up test fixtures."""
        self.encoder = FFmpegEncoder()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_available(self):
        """Test ffmpeg availability check."""
        # Just verify it returns a boolean
        result = self.encoder.is_available()
        self.assertIsInstance(result, bool)

    @patch('subprocess.run')
    def test_check_ffmpeg_available(self, mock_run):
        """Test ffmpeg detection when available."""
        mock_run.return_value = Mock(returncode=0)
        encoder = FFmpegEncoder()
        self.assertTrue(encoder._ffmpeg_available)

    @patch('subprocess.run')
    def test_check_ffmpeg_not_available(self, mock_run):
        """Test ffmpeg detection when not available."""
        mock_run.side_effect = FileNotFoundError()
        encoder = FFmpegEncoder()
        self.assertFalse(encoder._ffmpeg_available)

    @patch('subprocess.run')
    def test_encode_video_not_available(self, mock_run):
        """Test encode_video raises when ffmpeg not available."""
        mock_run.side_effect = FileNotFoundError()
        encoder = FFmpegEncoder()

        with self.assertRaises(RuntimeError) as ctx:
            encoder.encode_video(self.temp_dir, "output.mp4", 30)
        self.assertIn("ffmpeg not found", str(ctx.exception))

    @patch('subprocess.run')
    def test_encode_gif_not_available(self, mock_run):
        """Test encode_gif raises when ffmpeg not available."""
        mock_run.side_effect = FileNotFoundError()
        encoder = FFmpegEncoder()

        with self.assertRaises(RuntimeError) as ctx:
            encoder.encode_gif(self.temp_dir, "output.gif", 15)
        self.assertIn("ffmpeg not found", str(ctx.exception))


class TestProgressReporter(unittest.TestCase):
    """Test ProgressReporter."""

    def test_initialization(self):
        """Test reporter initialization."""
        reporter = ProgressReporter(100)
        self.assertEqual(reporter.total_frames, 100)
        self.assertEqual(reporter.current_frame, 0)

    def test_update_auto_increment(self):
        """Test auto-increment update."""
        reporter = ProgressReporter(100)
        reporter.update()
        self.assertEqual(reporter.current_frame, 1)
        reporter.update()
        self.assertEqual(reporter.current_frame, 2)

    def test_update_explicit(self):
        """Test explicit frame number update."""
        reporter = ProgressReporter(100)
        reporter.update(50)
        self.assertEqual(reporter.current_frame, 50)

    def test_callback_called(self):
        """Test callback is invoked."""
        callback = Mock()
        reporter = ProgressReporter(100, callback=callback)

        reporter.update(10)
        callback.assert_called_once_with(10, 100)

        reporter.update(20)
        self.assertEqual(callback.call_count, 2)
        callback.assert_called_with(20, 100)

    def test_no_callback_no_error(self):
        """Test update works without callback."""
        reporter = ProgressReporter(100)
        reporter.update()  # Should not raise

    def test_context_manager(self):
        """Test context manager usage."""
        reporter = ProgressReporter(10)

        with reporter:
            for i in range(10):
                reporter.update()

        self.assertEqual(reporter.current_frame, 10)


class TestPresetManager(unittest.TestCase):
    """Test PresetManager."""

    def test_get_preset_youtube_shorts(self):
        """Test getting YouTube Shorts preset."""
        preset = PresetManager.get_preset('youtube_shorts')
        self.assertEqual(preset.width, 1080)
        self.assertEqual(preset.height, 1920)
        self.assertEqual(preset.fps, 30)
        self.assertTrue(preset.is_vertical)

    def test_get_preset_youtube_1080p(self):
        """Test getting YouTube 1080p preset."""
        preset = PresetManager.get_preset('youtube_1080p')
        self.assertEqual(preset.width, 1920)
        self.assertEqual(preset.height, 1080)
        self.assertEqual(preset.fps, 30)
        self.assertFalse(preset.is_vertical)

    def test_get_preset_invalid(self):
        """Test getting invalid preset raises."""
        with self.assertRaises(ValueError) as ctx:
            PresetManager.get_preset('nonexistent')
        self.assertIn("Unknown preset", str(ctx.exception))

    def test_list_presets_all(self):
        """Test listing all presets."""
        presets = PresetManager.list_presets()
        self.assertIn('youtube_shorts', presets)
        self.assertIn('youtube_1080p', presets)
        self.assertIn('tiktok', presets)
        self.assertGreater(len(presets), 10)

    def test_list_presets_vertical_only(self):
        """Test listing only vertical presets."""
        presets = PresetManager.list_presets(filter_vertical=True)
        for name in presets:
            preset = PresetManager.get_preset(name)
            self.assertTrue(preset.is_vertical, f"{name} should be vertical")

    def test_list_presets_horizontal_only(self):
        """Test listing only horizontal presets."""
        presets = PresetManager.list_presets(filter_vertical=False)
        for name in presets:
            preset = PresetManager.get_preset(name)
            self.assertFalse(preset.is_vertical, f"{name} should be horizontal/square")

    def test_all_presets_have_required_fields(self):
        """Test all presets have required fields."""
        for name, preset in PresetManager.PRESETS.items():
            self.assertGreater(preset.width, 0, f"{name} width")
            self.assertGreater(preset.height, 0, f"{name} height")
            self.assertGreater(preset.fps, 0, f"{name} fps")
            self.assertGreaterEqual(preset.crf, 0, f"{name} crf")
            self.assertLessEqual(preset.crf, 51, f"{name} crf")


class MockVideoExporter(VideoExporter):
    """Concrete implementation of VideoExporter for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rendered_frames = []

    def render_frame(self, frame_num: int, temp_dir: str) -> str:
        """Mock render_frame implementation."""
        frame_path = Path(temp_dir) / f"frame_{frame_num:05d}.png"

        # Create a dummy image file
        from PIL import Image
        img = Image.new('RGB', (self.width, self.height), color='red')
        img.save(frame_path)

        self.rendered_frames.append(frame_num)
        return str(frame_path)


class TestVideoExporter(unittest.TestCase):
    """Test VideoExporter base class."""

    def test_initialization_with_duration(self):
        """Test initialization with duration."""
        exporter = MockVideoExporter("output.mp4", duration=10.0, fps=30)
        self.assertEqual(exporter.total_frames, 300)
        self.assertEqual(exporter.duration, 10.0)

    def test_initialization_with_total_frames(self):
        """Test initialization with total_frames."""
        exporter = MockVideoExporter("output.mp4", total_frames=300, fps=30)
        self.assertEqual(exporter.total_frames, 300)
        self.assertEqual(exporter.duration, 10.0)

    def test_initialization_requires_one_of(self):
        """Test initialization requires duration OR total_frames."""
        with self.assertRaises(ValueError):
            MockVideoExporter("output.mp4", fps=30)

    def test_initialization_not_both(self):
        """Test initialization rejects both duration AND total_frames."""
        with self.assertRaises(ValueError):
            MockVideoExporter("output.mp4", duration=10.0, total_frames=300, fps=30)

    def test_is_gif_detection_mp4(self):
        """Test MP4 format detection."""
        exporter = MockVideoExporter("output.mp4", duration=1.0)
        self.assertFalse(exporter.is_gif)

    def test_is_gif_detection_gif(self):
        """Test GIF format detection."""
        exporter = MockVideoExporter("output.gif", duration=1.0)
        self.assertTrue(exporter.is_gif)

    def test_from_preset(self):
        """Test creating exporter from preset."""
        exporter = MockVideoExporter.from_preset(
            'youtube_shorts',
            'output.mp4',
            duration=30.0
        )
        self.assertEqual(exporter.width, 1080)
        self.assertEqual(exporter.height, 1920)
        self.assertEqual(exporter.fps, 30)
        self.assertEqual(exporter.total_frames, 900)

    def test_from_preset_uses_max_duration(self):
        """Test from_preset uses preset's max_duration if not specified."""
        exporter = MockVideoExporter.from_preset(
            'youtube_shorts',
            'output.mp4'
        )
        # YouTube Shorts max is 60s
        self.assertEqual(exporter.duration, 60.0)

    def test_from_preset_requires_duration_for_unlimited(self):
        """Test from_preset requires duration for presets without max."""
        with self.assertRaises(ValueError):
            MockVideoExporter.from_preset(
                'youtube_1080p',  # No max_duration
                'output.mp4'
            )

    def test_from_preset_invalid_name(self):
        """Test from_preset with invalid preset name."""
        with self.assertRaises(ValueError):
            MockVideoExporter.from_preset(
                'invalid_preset',
                'output.mp4',
                duration=10.0
            )

    @patch('atari_style.core.video_base.FFmpegEncoder')
    def test_export_not_available_raises(self, mock_encoder_class):
        """Test export raises when ffmpeg not available."""
        mock_encoder = Mock()
        mock_encoder.is_available.return_value = False
        mock_encoder_class.return_value = mock_encoder

        exporter = MockVideoExporter("output.mp4", duration=1.0, fps=30)
        exporter.encoder = mock_encoder

        with self.assertRaises(RuntimeError) as ctx:
            exporter.export()
        self.assertIn("ffmpeg not found", str(ctx.exception))


class TestVideoExporterIntegration(unittest.TestCase):
    """Integration tests for VideoExporter (requires PIL)."""

    def setUp(self):
        """Set up test fixtures."""
        try:
            from PIL import Image
            self.has_pil = True
        except ImportError:
            self.has_pil = False

    def test_render_frames_called(self):
        """Test that render_frame is called for each frame."""
        if not self.has_pil:
            self.skipTest("PIL not available")

        exporter = MockVideoExporter("output.mp4", duration=0.1, fps=10)  # 1 frame

        # Mock the encoder to avoid actual ffmpeg calls
        with patch.object(exporter.encoder, 'is_available', return_value=True), \
             patch.object(exporter.encoder, 'encode_video', return_value=True), \
             patch('os.path.getsize', return_value=12345):
            exporter.export()

        self.assertEqual(len(exporter.rendered_frames), 1)
        self.assertEqual(exporter.rendered_frames[0], 0)


if __name__ == '__main__':
    unittest.main()
