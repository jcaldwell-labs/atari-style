"""Tests for GL video export, including thumbnail generation."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from atari_style.core.gl.video_export import (
    VideoExporter,
    VideoFormat,
    VIDEO_FORMATS,
    get_format_names,
)


class TestVideoFormat(unittest.TestCase):
    """Test VideoFormat dataclass."""

    def test_aspect_ratio_16_9(self):
        """Test 16:9 aspect ratio calculation."""
        fmt = VideoFormat(
            name='Test',
            width=1920,
            height=1080,
            fps=30,
            max_duration=None,
            description='Test format'
        )
        self.assertEqual(fmt.aspect_ratio, '16:9')

    def test_aspect_ratio_9_16(self):
        """Test 9:16 aspect ratio calculation."""
        fmt = VideoFormat(
            name='Test',
            width=1080,
            height=1920,
            fps=30,
            max_duration=None,
            description='Test format'
        )
        self.assertEqual(fmt.aspect_ratio, '9:16')

    def test_is_vertical(self):
        """Test vertical format detection."""
        vertical = VideoFormat(
            name='Vertical',
            width=1080,
            height=1920,
            fps=30,
            max_duration=None,
            description='Vertical'
        )
        horizontal = VideoFormat(
            name='Horizontal',
            width=1920,
            height=1080,
            fps=30,
            max_duration=None,
            description='Horizontal'
        )
        self.assertTrue(vertical.is_vertical)
        self.assertFalse(horizontal.is_vertical)

    def test_crf_default(self):
        """Test CRF default value."""
        fmt = VideoFormat(
            name='Test',
            width=1920,
            height=1080,
            fps=30,
            max_duration=None,
            description='Test'
        )
        self.assertEqual(fmt.crf, 18)

    def test_crf_custom(self):
        """Test custom CRF value."""
        fmt = VideoFormat(
            name='Test',
            width=1920,
            height=1080,
            fps=30,
            max_duration=None,
            description='Test',
            crf=28
        )
        self.assertEqual(fmt.crf, 28)


class TestVideoFormats(unittest.TestCase):
    """Test VIDEO_FORMATS presets."""

    def test_youtube_shorts_exists(self):
        """Test YouTube Shorts preset exists with correct values."""
        self.assertIn('youtube_shorts', VIDEO_FORMATS)
        fmt = VIDEO_FORMATS['youtube_shorts']
        self.assertEqual(fmt.width, 1080)
        self.assertEqual(fmt.height, 1920)
        self.assertEqual(fmt.max_duration, 60.0)

    def test_quality_presets_exist(self):
        """Test quality presets exist."""
        self.assertIn('high', VIDEO_FORMATS)
        self.assertIn('medium', VIDEO_FORMATS)
        self.assertIn('low', VIDEO_FORMATS)
        self.assertIn('preview', VIDEO_FORMATS)

    def test_quality_preset_crf_values(self):
        """Test quality presets have appropriate CRF values."""
        self.assertEqual(VIDEO_FORMATS['high'].crf, 18)
        self.assertEqual(VIDEO_FORMATS['medium'].crf, 23)
        self.assertEqual(VIDEO_FORMATS['low'].crf, 28)
        self.assertEqual(VIDEO_FORMATS['preview'].crf, 28)

    def test_platform_presets_exist(self):
        """Test platform presets exist."""
        self.assertIn('twitter', VIDEO_FORMATS)
        self.assertIn('discord', VIDEO_FORMATS)
        self.assertIn('instagram_story', VIDEO_FORMATS)

    def test_get_format_names(self):
        """Test get_format_names returns all presets."""
        names = get_format_names()
        self.assertIn('youtube_shorts', names)
        self.assertIn('high', names)
        self.assertIn('twitter', names)


class TestThumbnailGeneration(unittest.TestCase):
    """Test thumbnail generation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = VideoExporter(width=320, height=240, fps=30)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_thumbnail_invalid_composite(self):
        """Test create_thumbnail raises ValueError for unknown composite."""
        output_path = os.path.join(self.temp_dir, 'thumb.png')
        with self.assertRaises(ValueError) as context:
            self.exporter.create_thumbnail('nonexistent_composite', output_path)
        self.assertIn('nonexistent_composite', str(context.exception))

    def test_create_thumbnails_invalid_composite(self):
        """Test create_thumbnails raises ValueError for unknown composite."""
        with self.assertRaises(ValueError) as context:
            self.exporter.create_thumbnails('nonexistent', self.temp_dir, [0, 1])
        self.assertIn('nonexistent', str(context.exception))

    @patch('atari_style.core.gl.video_export.Image', None)
    def test_create_thumbnail_without_pillow(self):
        """Test create_thumbnail raises ImportError without Pillow."""
        output_path = os.path.join(self.temp_dir, 'thumb.png')
        with self.assertRaises(ImportError) as context:
            self.exporter.create_thumbnail('plasma_lissajous', output_path)
        self.assertIn('Pillow', str(context.exception))

    @patch('atari_style.core.gl.video_export.Image', None)
    def test_create_thumbnails_without_pillow(self):
        """Test create_thumbnails raises ImportError without Pillow."""
        with self.assertRaises(ImportError) as context:
            self.exporter.create_thumbnails('plasma_lissajous', self.temp_dir, [0])
        self.assertIn('Pillow', str(context.exception))


class TestThumbnailIntegration(unittest.TestCase):
    """Integration tests for thumbnail generation (requires GPU/Pillow)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Use small resolution for fast tests
        self.exporter = VideoExporter(width=64, height=64, fps=30)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_thumbnail_creates_file(self):
        """Test create_thumbnail creates output file."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        output_path = os.path.join(self.temp_dir, 'thumb.png')
        result = self.exporter.create_thumbnail('plasma_lissajous', output_path, timestamp=0.5)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

        # Verify image dimensions
        img = Image.open(output_path)
        self.assertEqual(img.size, (64, 64))

    def test_create_thumbnail_custom_resolution(self):
        """Test create_thumbnail respects custom resolution."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        output_path = os.path.join(self.temp_dir, 'thumb_custom.png')
        result = self.exporter.create_thumbnail(
            'plasma_lissajous', output_path,
            width=128, height=96
        )

        self.assertTrue(result)
        img = Image.open(output_path)
        self.assertEqual(img.size, (128, 96))

    def test_create_thumbnails_multiple(self):
        """Test create_thumbnails creates multiple files."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        timestamps = [0.0, 0.5, 1.0]
        result = self.exporter.create_thumbnails(
            'plasma_lissajous', self.temp_dir, timestamps
        )

        self.assertEqual(len(result), 3)
        for path in result:
            self.assertTrue(os.path.exists(path))

    def test_create_thumbnails_filename_format(self):
        """Test create_thumbnails uses correct filename format."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        timestamps = [2.5]
        result = self.exporter.create_thumbnails(
            'plasma_lissajous', self.temp_dir, timestamps
        )

        self.assertEqual(len(result), 1)
        self.assertIn('plasma_lissajous_2.5s.png', result[0])

    def test_create_thumbnails_custom_prefix(self):
        """Test create_thumbnails respects custom prefix."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        timestamps = [0.0]
        result = self.exporter.create_thumbnails(
            'plasma_lissajous', self.temp_dir, timestamps,
            prefix='custom'
        )

        self.assertEqual(len(result), 1)
        self.assertIn('custom_0.0s.png', result[0])

    def test_create_all_thumbnails(self):
        """Test create_all_thumbnails creates thumbnails for all composites."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        result = self.exporter.create_all_thumbnails(self.temp_dir)

        # Should have entry for each composite
        from atari_style.core.gl.composites import COMPOSITES
        self.assertEqual(len(result), len(COMPOSITES))

        # All should be successful
        for name, path in result.items():
            self.assertIsNotNone(path)
            self.assertTrue(os.path.exists(path))

    def test_create_thumbnail_creates_directory(self):
        """Test create_thumbnail creates output directory if needed."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not available")

        nested_path = os.path.join(self.temp_dir, 'nested', 'dir', 'thumb.png')
        result = self.exporter.create_thumbnail('plasma_lissajous', nested_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_path))


if __name__ == '__main__':
    unittest.main()
