"""Tests for the preview gallery module."""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from atari_style.preview.gallery import Gallery, MediaFile, format_bytes


class TestFormatBytes(unittest.TestCase):
    """Test format_bytes helper function."""

    def test_bytes(self):
        """Test formatting bytes."""
        self.assertEqual(format_bytes(0), '0.0 B')
        self.assertEqual(format_bytes(512), '512.0 B')
        self.assertEqual(format_bytes(1023), '1023.0 B')

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        self.assertEqual(format_bytes(1024), '1.0 KB')
        self.assertEqual(format_bytes(2048), '2.0 KB')
        self.assertEqual(format_bytes(1536), '1.5 KB')

    def test_megabytes(self):
        """Test formatting megabytes."""
        self.assertEqual(format_bytes(1024 * 1024), '1.0 MB')
        self.assertEqual(format_bytes(5 * 1024 * 1024), '5.0 MB')

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        self.assertEqual(format_bytes(1024 * 1024 * 1024), '1.0 GB')
        self.assertEqual(format_bytes(2 * 1024 * 1024 * 1024), '2.0 GB')

    def test_terabytes(self):
        """Test formatting terabytes."""
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), '1.0 TB')


class TestMediaFile(unittest.TestCase):
    """Test MediaFile dataclass."""

    def test_creation(self):
        """Test basic MediaFile creation."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=datetime(2025, 1, 1, 12, 0, 0),
        )
        self.assertEqual(mf.filename, 'video.mp4')
        self.assertEqual(mf.file_type, 'video')
        self.assertIsNone(mf.duration)

    def test_size_human_bytes(self):
        """Test human-readable size for bytes."""
        mf = MediaFile(
            path=Path('/test/small.txt'),
            filename='small.txt',
            file_type='image',
            extension='.txt',
            size_bytes=512,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.size_human, '512.0 B')

    def test_size_human_kilobytes(self):
        """Test human-readable size for kilobytes."""
        mf = MediaFile(
            path=Path('/test/medium.png'),
            filename='medium.png',
            file_type='image',
            extension='.png',
            size_bytes=2048,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.size_human, '2.0 KB')

    def test_size_human_megabytes(self):
        """Test human-readable size for megabytes."""
        mf = MediaFile(
            path=Path('/test/large.mp4'),
            filename='large.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=5 * 1024 * 1024,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.size_human, '5.0 MB')

    def test_duration_human_seconds(self):
        """Test human-readable duration for short clips."""
        mf = MediaFile(
            path=Path('/test/clip.mp4'),
            filename='clip.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1000,
            modified_time=datetime.now(),
            duration=45.0,
        )
        self.assertEqual(mf.duration_human, '45s')

    def test_duration_human_minutes(self):
        """Test human-readable duration for longer clips."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1000,
            modified_time=datetime.now(),
            duration=125.0,
        )
        self.assertEqual(mf.duration_human, '2:05')

    def test_duration_human_none(self):
        """Test human-readable duration when not set."""
        mf = MediaFile(
            path=Path('/test/image.png'),
            filename='image.png',
            file_type='image',
            extension='.png',
            size_bytes=1000,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.duration_human, '-')

    def test_resolution(self):
        """Test resolution string."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1000,
            modified_time=datetime.now(),
            width=1920,
            height=1080,
        )
        self.assertEqual(mf.resolution, '1920x1080')

    def test_resolution_none(self):
        """Test resolution when not set."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1000,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.resolution, '-')

    def test_unique_id_with_relative_path(self):
        """Test unique_id uses relative_path when available."""
        mf = MediaFile(
            path=Path('/test/subdir/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=datetime.now(),
            relative_path='subdir/video.mp4',
        )
        self.assertEqual(mf.unique_id, 'subdir/video.mp4')

    def test_unique_id_fallback_to_filename(self):
        """Test unique_id falls back to filename when no relative_path."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=datetime.now(),
        )
        self.assertEqual(mf.unique_id, 'video.mp4')

    def test_to_dict(self):
        """Test dictionary conversion."""
        now = datetime.now()
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=now,
            duration=60.0,
            width=1280,
            height=720,
        )
        d = mf.to_dict()
        self.assertEqual(d['filename'], 'video.mp4')
        self.assertEqual(d['file_type'], 'video')
        self.assertEqual(d['duration'], 60.0)
        self.assertEqual(d['resolution'], '1280x720')

    def test_to_dict_includes_unique_id(self):
        """Test dictionary includes unique_id and relative_path."""
        mf = MediaFile(
            path=Path('/test/subdir/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=datetime.now(),
            relative_path='subdir/video.mp4',
        )
        d = mf.to_dict()
        self.assertEqual(d['relative_path'], 'subdir/video.mp4')
        self.assertEqual(d['unique_id'], 'subdir/video.mp4')


class TestGallery(unittest.TestCase):
    """Test Gallery class."""

    def setUp(self):
        """Create temporary test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.gallery = Gallery(directories=[Path(self.temp_dir)])

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init_default_directory(self):
        """Test default directory initialization."""
        gallery = Gallery()
        self.assertEqual(len(gallery.directories), 1)
        self.assertEqual(gallery.directories[0].name, 'output')

    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        files = self.gallery.scan()
        self.assertEqual(len(files), 0)

    def test_scan_video_file(self):
        """Test scanning for video files."""
        # Create a dummy video file
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.write_bytes(b'fake video content')

        files = self.gallery.scan()

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].filename, 'test.mp4')
        self.assertEqual(files[0].file_type, 'video')
        self.assertEqual(files[0].extension, '.mp4')

    def test_scan_image_file(self):
        """Test scanning for image files."""
        # Create a dummy image file
        image_path = Path(self.temp_dir) / 'test.png'
        image_path.write_bytes(b'fake png content')

        files = self.gallery.scan()

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].filename, 'test.png')
        self.assertEqual(files[0].file_type, 'image')

    def test_scan_storyboard_json(self):
        """Test scanning for storyboard JSON files."""
        # Create a storyboard JSON
        json_path = Path(self.temp_dir) / 'storyboard.json'
        data = {
            'scenes': [
                {'effect': 'plasma', 'duration': 10},
                {'effect': 'mandelbrot', 'duration': 15},
            ]
        }
        json_path.write_text(json.dumps(data))

        files = self.gallery.scan()

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].filename, 'storyboard.json')
        self.assertEqual(files[0].file_type, 'storyboard')
        # Duration should be calculated from scenes
        self.assertEqual(files[0].duration, 25)

    def test_scan_input_script_json(self):
        """Test scanning for input script JSON files."""
        # Create an input script JSON
        json_path = Path(self.temp_dir) / 'input.json'
        data = {
            'duration': 15.0,
            'fps': 30,
            'keyframes': [
                {'time': 0.0, 'x': 0.0, 'y': 0.0},
                {'time': 1.0, 'x': 1.0, 'y': 0.0},
            ]
        }
        json_path.write_text(json.dumps(data))

        files = self.gallery.scan()

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].file_type, 'input_script')
        self.assertEqual(files[0].duration, 15.0)

    def test_scan_unsupported_file(self):
        """Test that unsupported files are ignored."""
        # Create unsupported file types
        (Path(self.temp_dir) / 'readme.txt').write_text('readme')
        (Path(self.temp_dir) / 'script.py').write_text('print()')

        files = self.gallery.scan()

        self.assertEqual(len(files), 0)

    def test_scan_invalid_json(self):
        """Test handling of invalid JSON files."""
        json_path = Path(self.temp_dir) / 'invalid.json'
        json_path.write_text('{ invalid json }')

        files = self.gallery.scan()

        self.assertEqual(len(files), 0)

    def test_filter_by_type(self):
        """Test filtering files by type."""
        # Create various file types
        (Path(self.temp_dir) / 'video1.mp4').write_bytes(b'video')
        (Path(self.temp_dir) / 'video2.mp4').write_bytes(b'video')
        (Path(self.temp_dir) / 'image.png').write_bytes(b'image')

        self.gallery.scan()

        videos = self.gallery.filter_by_type('video')
        images = self.gallery.filter_by_type('image')

        self.assertEqual(len(videos), 2)
        self.assertEqual(len(images), 1)

    def test_get_by_filename(self):
        """Test getting file by filename."""
        (Path(self.temp_dir) / 'target.mp4').write_bytes(b'video')
        (Path(self.temp_dir) / 'other.mp4').write_bytes(b'video')

        self.gallery.scan()

        result = self.gallery.get_by_filename('target.mp4')

        self.assertIsNotNone(result)
        self.assertEqual(result.filename, 'target.mp4')

    def test_get_by_filename_not_found(self):
        """Test getting non-existent file."""
        self.gallery.scan()

        result = self.gallery.get_by_filename('missing.mp4')

        self.assertIsNone(result)

    def test_get_by_id(self):
        """Test getting file by unique_id."""
        (Path(self.temp_dir) / 'target.mp4').write_bytes(b'video')

        self.gallery.scan()

        result = self.gallery.get_by_id('target.mp4')

        self.assertIsNotNone(result)
        self.assertEqual(result.filename, 'target.mp4')

    def test_get_by_id_with_subdirectory(self):
        """Test getting file by unique_id in subdirectory."""
        import os
        subdir = Path(self.temp_dir) / 'subdir'
        subdir.mkdir()
        (subdir / 'video.mp4').write_bytes(b'video')

        self.gallery.scan()

        # Path separators are OS-specific
        expected_path = os.path.join('subdir', 'video.mp4')
        result = self.gallery.get_by_id(expected_path)

        self.assertIsNotNone(result)
        self.assertEqual(result.filename, 'video.mp4')
        self.assertEqual(result.relative_path, expected_path)

    def test_get_by_id_not_found(self):
        """Test getting non-existent file by id."""
        self.gallery.scan()

        result = self.gallery.get_by_id('missing/file.mp4')

        self.assertIsNone(result)

    def test_duplicate_filenames_in_subdirectories(self):
        """Test handling duplicate filenames in different subdirectories."""
        import os
        # Create same filename in two different subdirectories
        subdir1 = Path(self.temp_dir) / 'project1'
        subdir2 = Path(self.temp_dir) / 'project2'
        subdir1.mkdir()
        subdir2.mkdir()

        (subdir1 / 'output.mp4').write_bytes(b'video1')
        (subdir2 / 'output.mp4').write_bytes(b'video2')

        files = self.gallery.scan()

        # Should find both files
        self.assertEqual(len(files), 2)

        # Each should have unique relative_path (OS-specific separators)
        paths = {f.relative_path for f in files}
        expected_path1 = os.path.join('project1', 'output.mp4')
        expected_path2 = os.path.join('project2', 'output.mp4')
        self.assertIn(expected_path1, paths)
        self.assertIn(expected_path2, paths)

        # Both have same filename
        filenames = {f.filename for f in files}
        self.assertEqual(filenames, {'output.mp4'})

        # Can retrieve each by unique_id
        file1 = self.gallery.get_by_id(expected_path1)
        file2 = self.gallery.get_by_id(expected_path2)

        self.assertIsNotNone(file1)
        self.assertIsNotNone(file2)
        self.assertNotEqual(file1.path, file2.path)

    def test_get_summary(self):
        """Test summary statistics."""
        # Create various file types
        (Path(self.temp_dir) / 'video.mp4').write_bytes(b'v' * 1000)
        (Path(self.temp_dir) / 'image.png').write_bytes(b'i' * 500)
        data = {'scenes': [{'effect': 'test', 'duration': 5}]}
        (Path(self.temp_dir) / 'story.json').write_text(json.dumps(data))

        self.gallery.scan()
        summary = self.gallery.get_summary()

        self.assertEqual(summary['total_files'], 3)
        self.assertEqual(summary['by_type']['video']['count'], 1)
        self.assertEqual(summary['by_type']['image']['count'], 1)
        self.assertEqual(summary['by_type']['storyboard']['count'], 1)

    def test_scan_sorts_by_modified_time(self):
        """Test that files are sorted by modification time (newest first)."""
        import time

        # Create files with different modification times
        old_file = Path(self.temp_dir) / 'old.mp4'
        old_file.write_bytes(b'old')

        time.sleep(0.1)

        new_file = Path(self.temp_dir) / 'new.mp4'
        new_file.write_bytes(b'new')

        files = self.gallery.scan()

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].filename, 'new.mp4')
        self.assertEqual(files[1].filename, 'old.mp4')


class TestGalleryProbing(unittest.TestCase):
    """Test Gallery probing functionality."""

    def test_check_ffprobe_not_available(self):
        """Test handling when ffprobe is not available."""
        gallery = Gallery(directories=[Path('.')])

        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = gallery._check_ffprobe()

        self.assertFalse(result)

    def test_check_ffprobe_available(self):
        """Test when ffprobe is available."""
        gallery = Gallery(directories=[Path('.')])

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result):
            result = gallery._check_ffprobe()

        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
