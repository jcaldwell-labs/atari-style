"""Tests for showcase generator module."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from atari_style.core.showcase import (
    ShowcaseEntry,
    ShowcaseManifest,
    TitleCardGenerator,
    ShowcaseGenerator,
    create_showcase,
)


class TestShowcaseEntry(unittest.TestCase):
    """Test ShowcaseEntry dataclass."""

    def test_entry_creation(self):
        """Test basic entry creation."""
        entry = ShowcaseEntry(video_path="demo.mp4")
        self.assertEqual(entry.video_path, "demo.mp4")
        self.assertIsNone(entry.title)
        self.assertEqual(entry.title_duration, 2.0)

    def test_entry_with_title(self):
        """Test entry with title."""
        entry = ShowcaseEntry(
            video_path="demo.mp4",
            title="Demo Title",
            title_duration=3.5,
        )
        self.assertEqual(entry.title, "Demo Title")
        self.assertEqual(entry.title_duration, 3.5)


class TestShowcaseManifest(unittest.TestCase):
    """Test ShowcaseManifest class."""

    def test_manifest_defaults(self):
        """Test manifest with default values."""
        manifest = ShowcaseManifest()
        self.assertEqual(manifest.entries, [])
        self.assertEqual(manifest.output_path, "showcase.mp4")
        self.assertEqual(manifest.title_duration, 2.0)
        self.assertEqual(manifest.title_style, "terminal")
        self.assertEqual(manifest.fps, 30)
        self.assertEqual(manifest.width, 800)
        self.assertEqual(manifest.height, 480)

    def test_manifest_from_json_simple(self):
        """Test loading manifest from simple JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'entries': ['demo1.mp4', 'demo2.mp4'],
                'output': 'output.mp4',
            }, f)
            temp_path = f.name

        try:
            manifest = ShowcaseManifest.from_json(temp_path)
            self.assertEqual(len(manifest.entries), 2)
            self.assertEqual(manifest.entries[0].video_path, 'demo1.mp4')
            self.assertEqual(manifest.entries[1].video_path, 'demo2.mp4')
            self.assertEqual(manifest.output_path, 'output.mp4')
        finally:
            os.unlink(temp_path)

    def test_manifest_from_json_with_titles(self):
        """Test loading manifest with title entries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'entries': [
                    {'video': 'demo1.mp4', 'title': 'Demo 1'},
                    {'video': 'demo2.mp4', 'title': 'Demo 2', 'title_duration': 3.0},
                ],
                'output': 'output.mp4',
                'title_style': 'minimal',
            }, f)
            temp_path = f.name

        try:
            manifest = ShowcaseManifest.from_json(temp_path)
            self.assertEqual(len(manifest.entries), 2)
            self.assertEqual(manifest.entries[0].title, 'Demo 1')
            self.assertEqual(manifest.entries[1].title, 'Demo 2')
            self.assertEqual(manifest.entries[1].title_duration, 3.0)
            self.assertEqual(manifest.title_style, 'minimal')
        finally:
            os.unlink(temp_path)

    def test_manifest_to_json(self):
        """Test saving manifest to JSON."""
        manifest = ShowcaseManifest(
            entries=[
                ShowcaseEntry(video_path='demo1.mp4', title='Demo 1'),
                ShowcaseEntry(video_path='demo2.mp4'),
            ],
            output_path='showcase.mp4',
            fps=60,
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            manifest.to_json(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            self.assertEqual(data['output'], 'showcase.mp4')
            self.assertEqual(data['fps'], 60)
            self.assertEqual(len(data['entries']), 2)
            self.assertEqual(data['entries'][0]['title'], 'Demo 1')
            # Second entry without title should be just the path
            self.assertEqual(data['entries'][1], 'demo2.mp4')
        finally:
            os.unlink(temp_path)


class TestTitleCardGenerator(unittest.TestCase):
    """Test TitleCardGenerator class."""

    def test_generator_init(self):
        """Test generator initialization."""
        gen = TitleCardGenerator(width=1920, height=1080, fps=60, style='minimal')
        self.assertEqual(gen.width, 1920)
        self.assertEqual(gen.height, 1080)
        self.assertEqual(gen.fps, 60)
        self.assertEqual(gen.style, 'minimal')

    def test_grid_dimensions(self):
        """Test terminal grid dimension calculations."""
        gen = TitleCardGenerator(width=800, height=480)
        # 800 / 10 = 80 columns, 480 / 20 = 24 rows
        self.assertEqual(gen.grid_width, 80)
        self.assertEqual(gen.grid_height, 24)

    @patch('atari_style.core.showcase.PIL_AVAILABLE', True)
    @patch('atari_style.core.showcase.subprocess.run')
    def test_generate_calls_ffmpeg(self, mock_run):
        """Test that generate calls ffmpeg."""
        mock_run.return_value = MagicMock(returncode=0)

        gen = TitleCardGenerator()

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            output_path = f.name

        try:
            gen.generate("Test Title", 2.0, output_path)

            # Verify ffmpeg was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args[0], 'ffmpeg')
            self.assertIn('-t', call_args)
            self.assertIn('2.0', call_args)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestShowcaseGenerator(unittest.TestCase):
    """Test ShowcaseGenerator class."""

    def test_generator_init(self):
        """Test generator initialization."""
        manifest = ShowcaseManifest()
        gen = ShowcaseGenerator(manifest)
        self.assertEqual(gen.manifest, manifest)
        self.assertIsNotNone(gen.title_generator)

    @patch('shutil.which')
    def test_check_ffmpeg_available(self, mock_which):
        """Test ffmpeg availability check."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        manifest = ShowcaseManifest()
        gen = ShowcaseGenerator(manifest)
        self.assertTrue(gen._check_ffmpeg())

    @patch('shutil.which')
    def test_check_ffmpeg_missing(self, mock_which):
        """Test ffmpeg missing check."""
        mock_which.return_value = None
        manifest = ShowcaseManifest()
        gen = ShowcaseGenerator(manifest)
        self.assertFalse(gen._check_ffmpeg())

    @patch('shutil.which')
    def test_generate_raises_without_ffmpeg(self, mock_which):
        """Test generate raises if ffmpeg not found."""
        mock_which.return_value = None
        manifest = ShowcaseManifest(entries=[ShowcaseEntry(video_path='demo.mp4')])
        gen = ShowcaseGenerator(manifest)

        with self.assertRaises(RuntimeError) as ctx:
            gen.generate()
        self.assertIn('ffmpeg', str(ctx.exception))

    @patch('shutil.which')
    def test_generate_raises_with_empty_manifest(self, mock_which):
        """Test generate raises with empty manifest."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        manifest = ShowcaseManifest()
        gen = ShowcaseGenerator(manifest)

        with self.assertRaises(ValueError) as ctx:
            gen.generate()
        self.assertIn('No entries', str(ctx.exception))

    @patch('shutil.which')
    def test_generate_raises_with_missing_file(self, mock_which):
        """Test generate raises if video file missing."""
        mock_which.return_value = '/usr/bin/ffmpeg'
        manifest = ShowcaseManifest(
            entries=[ShowcaseEntry(video_path='nonexistent.mp4')]
        )
        gen = ShowcaseGenerator(manifest)

        with self.assertRaises(FileNotFoundError):
            gen.generate()


class TestCreateShowcase(unittest.TestCase):
    """Test create_showcase convenience function."""

    def test_raises_on_title_count_mismatch(self):
        """Test raises if title count doesn't match videos."""
        with self.assertRaises(ValueError) as ctx:
            create_showcase(
                input_videos=['a.mp4', 'b.mp4'],
                output_path='out.mp4',
                titles=['Only One Title'],
            )
        self.assertIn('titles', str(ctx.exception).lower())


class TestManifestRoundTrip(unittest.TestCase):
    """Test manifest JSON round-trip."""

    def test_roundtrip_preserves_data(self):
        """Test that save/load preserves all data."""
        original = ShowcaseManifest(
            entries=[
                ShowcaseEntry(video_path='demo1.mp4', title='Demo 1', title_duration=1.5),
                ShowcaseEntry(video_path='demo2.mp4'),
            ],
            output_path='showcase.mp4',
            title_duration=2.5,
            title_style='minimal',
            fps=60,
            width=1920,
            height=1080,
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            original.to_json(temp_path)
            loaded = ShowcaseManifest.from_json(temp_path)

            self.assertEqual(loaded.output_path, original.output_path)
            self.assertEqual(loaded.title_duration, original.title_duration)
            self.assertEqual(loaded.title_style, original.title_style)
            self.assertEqual(loaded.fps, original.fps)
            self.assertEqual(loaded.width, original.width)
            self.assertEqual(loaded.height, original.height)
            self.assertEqual(len(loaded.entries), len(original.entries))
            self.assertEqual(loaded.entries[0].title, 'Demo 1')
            self.assertEqual(loaded.entries[0].title_duration, 1.5)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
