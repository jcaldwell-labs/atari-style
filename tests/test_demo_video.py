"""Tests for demo video exporter, including GIF export."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from atari_style.core.demo_video import (
    DemoVideoExporter,
    DEMO_REGISTRY,
    register_demo,
)


class TestDemoVideoExporterInit(unittest.TestCase):
    """Test DemoVideoExporter initialization."""

    def setUp(self):
        """Create a temporary script file for testing."""
        self.script_data = {
            'name': 'Test Script',
            'duration': 2.0,
            'fps': 30,
            'keyframes': [
                {'time': 0.0, 'x': 0.0, 'y': 0.0, 'buttons': []},
                {'time': 1.0, 'x': 1.0, 'y': 1.0, 'buttons': [0]},
            ]
        }
        self.temp_script = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        json.dump(self.script_data, self.temp_script)
        self.temp_script.flush()
        self.temp_script.close()

    def tearDown(self):
        """Clean up temp file."""
        os.unlink(self.temp_script.name)

    def test_gif_mode_defaults(self):
        """Test GIF mode default settings."""
        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        self.assertTrue(exporter.gif_mode)
        self.assertEqual(exporter.gif_fps, DemoVideoExporter.DEFAULT_GIF_FPS)
        self.assertEqual(exporter.gif_scale, DemoVideoExporter.DEFAULT_GIF_MAX_WIDTH)

    def test_gif_mode_custom_fps(self):
        """Test GIF mode with custom FPS."""
        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_fps=10,
        )

        self.assertEqual(exporter.gif_fps, 10)

    def test_gif_mode_custom_scale(self):
        """Test GIF mode with custom scale."""
        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_scale=320,
        )

        self.assertEqual(exporter.gif_scale, 320)

    def test_video_mode_ignores_gif_settings(self):
        """Test that video mode doesn't use GIF settings for encoding."""
        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.mp4',
            gif_mode=False,
        )

        self.assertFalse(exporter.gif_mode)

    def test_unknown_demo_raises_error(self):
        """Test that unknown demo name raises ValueError."""
        with self.assertRaises(ValueError) as context:
            DemoVideoExporter(
                demo_name='nonexistent_demo',
                script_path=self.temp_script.name,
                output_path='/tmp/test.mp4',
            )

        self.assertIn('nonexistent_demo', str(context.exception))
        self.assertIn('Available', str(context.exception))


class TestDemoVideoExporterEncode(unittest.TestCase):
    """Test encoding methods with FFmpegEncoder."""

    def setUp(self):
        """Create a temporary script file for testing."""
        self.script_data = {
            'name': 'Test Script',
            'duration': 0.5,  # Very short for fast tests
            'fps': 10,
            'keyframes': [
                {'time': 0.0, 'x': 0.0, 'y': 0.0, 'buttons': []},
            ]
        }
        self.temp_script = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        json.dump(self.script_data, self.temp_script)
        self.temp_script.flush()
        self.temp_script.close()

    def tearDown(self):
        """Clean up temp file."""
        os.unlink(self.temp_script.name)

    @patch('atari_style.core.demo_video.FFmpegEncoder')
    def test_exporter_uses_encoder_for_gif(self, mock_encoder_class):
        """Test that GIF encoding uses FFmpegEncoder.encode_gif."""
        mock_encoder = MagicMock()
        mock_encoder.is_available.return_value = True
        mock_encoder.encode_gif.return_value = True
        mock_encoder_class.return_value = mock_encoder

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        # The encoder should be created
        mock_encoder_class.assert_called_once()

    @patch('atari_style.core.demo_video.FFmpegEncoder')
    def test_gif_uses_fps_setting(self, mock_encoder_class):
        """Test that GIF encoding respects fps setting."""
        mock_encoder = MagicMock()
        mock_encoder.is_available.return_value = True
        mock_encoder_class.return_value = mock_encoder

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_fps=20,
        )

        # Check fps is stored correctly
        self.assertEqual(exporter.gif_fps, 20)

    @patch('atari_style.core.demo_video.FFmpegEncoder')
    def test_gif_uses_scale_setting(self, mock_encoder_class):
        """Test that GIF encoding respects scale setting."""
        mock_encoder = MagicMock()
        mock_encoder.is_available.return_value = True
        mock_encoder_class.return_value = mock_encoder

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_scale=320,
        )

        # Check scale is stored correctly
        self.assertEqual(exporter.gif_scale, 320)

    @patch('atari_style.core.demo_video.FFmpegEncoder')
    def test_export_raises_without_ffmpeg(self, mock_encoder_class):
        """Test that missing ffmpeg raises RuntimeError on export."""
        mock_encoder = MagicMock()
        mock_encoder.is_available.return_value = False
        mock_encoder_class.return_value = mock_encoder

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        with self.assertRaises(RuntimeError) as context:
            exporter.export()

        self.assertIn('ffmpeg not found', str(context.exception))

    @patch('atari_style.core.demo_video.FFmpegEncoder')
    def test_export_raises_on_encode_failure(self, mock_encoder_class):
        """Test that encoding failure raises RuntimeError."""
        mock_encoder = MagicMock()
        mock_encoder.is_available.return_value = True
        mock_encoder.encode_gif.return_value = False
        mock_encoder_class.return_value = mock_encoder

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        with self.assertRaises(RuntimeError) as context:
            exporter.export()

        self.assertIn('ffmpeg encoding failed', str(context.exception))


class TestDemoRegistry(unittest.TestCase):
    """Test demo registry functionality."""

    def test_joystick_test_registered(self):
        """Test that joystick_test is in the registry."""
        self.assertIn('joystick_test', DEMO_REGISTRY)

    def test_starfield_registered(self):
        """Test that starfield is in the registry."""
        self.assertIn('starfield', DEMO_REGISTRY)
        self.assertIn('factory', DEMO_REGISTRY['starfield'])
        self.assertIn('description', DEMO_REGISTRY['starfield'])

    def test_platonic_solids_registered(self):
        """Test that platonic_solids is in the registry."""
        self.assertIn('platonic_solids', DEMO_REGISTRY)
        self.assertIn('factory', DEMO_REGISTRY['platonic_solids'])
        self.assertIn('description', DEMO_REGISTRY['platonic_solids'])

    def test_registry_has_description(self):
        """Test that registered demos have descriptions."""
        for name, info in DEMO_REGISTRY.items():
            self.assertIn('description', info)
            self.assertIn('factory', info)


if __name__ == '__main__':
    unittest.main()
