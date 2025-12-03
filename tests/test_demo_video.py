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
    """Test encoding methods."""

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

    @patch('atari_style.core.demo_video.subprocess.run')
    @patch('atari_style.core.demo_video.shutil.which')
    def test_encode_gif_calls_ffmpeg_twice(self, mock_which, mock_run):
        """Test that GIF encoding uses two-pass approach."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        mock_run.return_value = MagicMock(returncode=0, stderr='')

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        # Call the private method directly
        exporter._encode_gif('/tmp/frames')

        # Should be called twice: once for palette, once for GIF
        self.assertEqual(mock_run.call_count, 2)

        # Check first call is palette generation
        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn('palettegen', ' '.join(first_call_args))

        # Check second call is GIF encoding
        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertIn('paletteuse', ' '.join(second_call_args))

    @patch('atari_style.core.demo_video.subprocess.run')
    @patch('atari_style.core.demo_video.shutil.which')
    def test_encode_gif_uses_fps_setting(self, mock_which, mock_run):
        """Test that GIF encoding respects fps setting."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        mock_run.return_value = MagicMock(returncode=0, stderr='')

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_fps=20,
        )

        exporter._encode_gif('/tmp/frames')

        # Check fps is in the filter string
        first_call_args = mock_run.call_args_list[0][0][0]
        filter_arg = [a for a in first_call_args if 'fps=20' in a]
        self.assertTrue(len(filter_arg) > 0, "fps=20 should be in filter arguments")

    @patch('atari_style.core.demo_video.subprocess.run')
    @patch('atari_style.core.demo_video.shutil.which')
    def test_encode_gif_uses_scale_setting(self, mock_which, mock_run):
        """Test that GIF encoding respects scale setting."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        mock_run.return_value = MagicMock(returncode=0, stderr='')

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
            gif_scale=320,
        )

        exporter._encode_gif('/tmp/frames')

        # Check scale is in the filter string
        first_call_args = mock_run.call_args_list[0][0][0]
        filter_arg = [a for a in first_call_args if 'scale=320' in a]
        self.assertTrue(len(filter_arg) > 0, "scale=320 should be in filter arguments")

    @patch('atari_style.core.demo_video.shutil.which')
    def test_encode_gif_raises_without_ffmpeg(self, mock_which):
        """Test that missing ffmpeg raises RuntimeError."""
        mock_which.return_value = None

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        with self.assertRaises(RuntimeError) as context:
            exporter._encode_gif('/tmp/frames')

        self.assertIn('ffmpeg not found', str(context.exception))

    @patch('atari_style.core.demo_video.subprocess.run')
    @patch('atari_style.core.demo_video.shutil.which')
    def test_encode_gif_raises_on_palette_failure(self, mock_which, mock_run):
        """Test that palette generation failure raises RuntimeError."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        mock_run.return_value = MagicMock(returncode=1, stderr='palette error')

        exporter = DemoVideoExporter(
            demo_name='joystick_test',
            script_path=self.temp_script.name,
            output_path='/tmp/test.gif',
            gif_mode=True,
        )

        with self.assertRaises(RuntimeError) as context:
            exporter._encode_gif('/tmp/frames')

        self.assertIn('palette generation failed', str(context.exception))


class TestDemoRegistry(unittest.TestCase):
    """Test demo registry functionality."""

    def test_joystick_test_registered(self):
        """Test that joystick_test is in the registry."""
        self.assertIn('joystick_test', DEMO_REGISTRY)

    def test_registry_has_description(self):
        """Test that registered demos have descriptions."""
        for name, info in DEMO_REGISTRY.items():
            self.assertIn('description', info)
            self.assertIn('factory', info)


if __name__ == '__main__':
    unittest.main()
