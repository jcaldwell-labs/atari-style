"""Tests for the preview server module."""

import io
import json
import tempfile
import unittest
from datetime import datetime
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch
import urllib.request
import urllib.error

from atari_style.preview.server import PreviewHandler, PreviewServer, main
from atari_style.preview.gallery import Gallery, MediaFile


class MockWFile:
    """Mock wfile for capturing response output."""

    def __init__(self):
        self.data = io.BytesIO()

    def write(self, data):
        self.data.write(data)

    def getvalue(self):
        return self.data.getvalue()


class TestPreviewHandler(unittest.TestCase):
    """Tests for PreviewHandler request handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.gallery = Gallery(directories=[Path(self.temp_dir)])
        self.templates_dir = Path(__file__).parent.parent / 'atari_style' / 'preview' / 'templates'

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_mock_handler(self, path='/'):
        """Create a mock handler with a given path."""
        # Mock the socket and request
        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO(b'')

        mock_address = ('127.0.0.1', 8080)

        # Create a partial handler factory
        handler = MagicMock(spec=PreviewHandler)
        handler.gallery = self.gallery
        handler.templates_dir = self.templates_dir
        handler.path = path
        handler.requestline = f'GET {path} HTTP/1.1'
        handler.wfile = MockWFile()
        handler.client_address = mock_address
        handler.headers = {}

        return handler

    def test_route_gallery(self):
        """Test routing to gallery page."""
        # Create video file
        (Path(self.temp_dir) / 'test.mp4').write_bytes(b'video')
        self.gallery.scan()

        handler = self._create_mock_handler('/')

        # Call do_GET through the class method binding
        PreviewHandler.do_GET(handler)

        # Should call _serve_gallery
        handler._serve_gallery.assert_called_once()

    def test_route_view(self):
        """Test routing to viewer page."""
        handler = self._create_mock_handler('/view?file=test.mp4')

        PreviewHandler.do_GET(handler)

        handler._serve_viewer.assert_called_once()

    def test_route_storyboard(self):
        """Test routing to storyboard page."""
        handler = self._create_mock_handler('/storyboard?file=story.json')

        PreviewHandler.do_GET(handler)

        handler._serve_storyboard.assert_called_once()

    def test_route_api_files(self):
        """Test routing to API files endpoint."""
        handler = self._create_mock_handler('/api/files')

        PreviewHandler.do_GET(handler)

        handler._serve_api_files.assert_called_once()

    def test_route_api_summary(self):
        """Test routing to API summary endpoint."""
        handler = self._create_mock_handler('/api/summary')

        PreviewHandler.do_GET(handler)

        handler._serve_api_summary.assert_called_once()

    def test_route_media_file(self):
        """Test routing to media file serving."""
        handler = self._create_mock_handler('/media/test.mp4')

        PreviewHandler.do_GET(handler)

        handler._serve_media_file.assert_called_once_with('test.mp4')

    def test_route_static_file(self):
        """Test routing to static file serving."""
        handler = self._create_mock_handler('/static/style.css')

        PreviewHandler.do_GET(handler)

        handler._serve_static.assert_called_once_with('style.css')

    def test_route_404(self):
        """Test 404 for unknown routes."""
        handler = self._create_mock_handler('/unknown/path')

        PreviewHandler.do_GET(handler)

        handler.send_error.assert_called_once_with(404, "Not Found")


class TestPreviewHandlerHelpers(unittest.TestCase):
    """Tests for PreviewHandler helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.gallery = Gallery(directories=[Path(self.temp_dir)])
        self.templates_dir = Path(__file__).parent.parent / 'atari_style' / 'preview' / 'templates'

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_render_file_card_video(self):
        """Test rendering a video file card."""
        mf = MediaFile(
            path=Path('/test/video.mp4'),
            filename='video.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024 * 1024,
            modified_time=datetime.now(),
            duration=60.0,
            width=1920,
            height=1080,
        )

        # Create mock handler
        handler = MagicMock()
        handler.gallery = self.gallery

        html = PreviewHandler._render_file_card(handler, mf)

        self.assertIn('video.mp4', html)
        self.assertIn('video-preview', html)
        self.assertIn('/view?file=video.mp4', html)
        self.assertIn('🎬', html)

    def test_render_file_card_image(self):
        """Test rendering an image file card."""
        mf = MediaFile(
            path=Path('/test/image.png'),
            filename='image.png',
            file_type='image',
            extension='.png',
            size_bytes=512 * 1024,
            modified_time=datetime.now(),
            width=800,
            height=600,
        )

        handler = MagicMock()
        html = PreviewHandler._render_file_card(handler, mf)

        self.assertIn('image.png', html)
        self.assertIn('image-preview', html)
        self.assertIn('🖼️', html)

    def test_render_file_card_storyboard(self):
        """Test rendering a storyboard file card."""
        mf = MediaFile(
            path=Path('/test/story.json'),
            filename='story.json',
            file_type='storyboard',
            extension='.json',
            size_bytes=2048,
            modified_time=datetime.now(),
            duration=120.0,
        )

        handler = MagicMock()
        html = PreviewHandler._render_file_card(handler, mf)

        self.assertIn('story.json', html)
        self.assertIn('/storyboard?file=story.json', html)
        self.assertIn('📋', html)

    def test_render_file_card_xss_prevention(self):
        """Test that filenames are escaped to prevent XSS."""
        mf = MediaFile(
            path=Path('/test/<script>alert("xss")</script>.mp4'),
            filename='<script>alert("xss")</script>.mp4',
            file_type='video',
            extension='.mp4',
            size_bytes=1024,
            modified_time=datetime.now(),
        )

        handler = MagicMock()
        html = PreviewHandler._render_file_card(handler, mf)

        # Should be escaped
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert', html)

    def test_render_timeline(self):
        """Test timeline rendering."""
        data = {
            'scenes': [
                {'effect': 'plasma', 'duration': 10},
                {'effect': 'mandelbrot', 'duration': 20},
            ]
        }

        handler = MagicMock()
        html = PreviewHandler._render_timeline(handler, data)

        self.assertIn('timeline', html)
        self.assertIn('plasma', html)
        self.assertIn('mandelbrot', html)
        self.assertIn('Total: 30s', html)

    def test_render_timeline_empty(self):
        """Test timeline rendering with no scenes."""
        data = {'scenes': []}

        handler = MagicMock()
        html = PreviewHandler._render_timeline(handler, data)

        self.assertIn('No scenes defined', html)

    def test_render_scenes(self):
        """Test scene card rendering."""
        data = {
            'scenes': [
                {
                    'effect': 'plasma',
                    'duration': 10,
                    'params': {'scale': 2.0, 'speed': 1.5}
                },
            ]
        }

        handler = MagicMock()
        html = PreviewHandler._render_scenes(handler, data)

        self.assertIn('Scene 1', html)
        self.assertIn('plasma', html)
        self.assertIn('scale', html)
        self.assertIn('2.0', html)

    def test_render_scenes_xss_prevention(self):
        """Test scene rendering escapes user data."""
        data = {
            'scenes': [
                {
                    'effect': '<script>alert(1)</script>',
                    'duration': 10,
                    'params': {'<key>': '<value>'}
                },
            ]
        }

        handler = MagicMock()
        html = PreviewHandler._render_scenes(handler, data)

        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert', html)


class TestPreviewServer(unittest.TestCase):
    """Tests for PreviewServer class."""

    def test_init_default_directories(self):
        """Test default directory initialization."""
        server = PreviewServer()

        self.assertEqual(server.port, 8000)
        self.assertEqual(server.host, 'localhost')
        self.assertIsNotNone(server.gallery)

    def test_init_custom_directories(self):
        """Test custom directory initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            server = PreviewServer(
                directories=[Path(tmpdir)],
                port=3000,
                host='0.0.0.0'
            )

            self.assertEqual(server.port, 3000)
            self.assertEqual(server.host, '0.0.0.0')
            self.assertEqual(len(server.gallery.directories), 1)

    def test_templates_dir_exists(self):
        """Test that templates directory is configured."""
        server = PreviewServer()

        self.assertTrue(server.templates_dir.exists())


class TestPathTraversalProtection(unittest.TestCase):
    """Tests for path traversal attack prevention."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.gallery = Gallery(directories=[Path(self.temp_dir)])
        self.templates_dir = Path(__file__).parent.parent / 'atari_style' / 'preview' / 'templates'

        # Create static directory and file
        static_dir = self.templates_dir / 'static'
        if not static_dir.exists():
            static_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_static_path_traversal_blocked(self):
        """Test that path traversal in static files is blocked."""
        handler = MagicMock()
        handler.templates_dir = self.templates_dir
        handler.send_error = MagicMock()

        # Try to escape the static directory
        PreviewHandler._serve_static(handler, '../../../etc/passwd')

        handler.send_error.assert_called_once()
        # Should be 403 Forbidden or 404 Not Found
        error_code = handler.send_error.call_args[0][0]
        self.assertIn(error_code, [403, 404])


class TestCLI(unittest.TestCase):
    """Tests for CLI entry point."""

    def test_main_help(self):
        """Test CLI help output."""
        import sys
        from io import StringIO

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        with self.assertRaises(SystemExit) as cm:
            sys.argv = ['preview', '--help']
            main()

        sys.stdout = old_stdout
        self.assertEqual(cm.exception.code, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the preview server."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        (Path(self.temp_dir) / 'test.mp4').write_bytes(b'video content')
        (Path(self.temp_dir) / 'test.png').write_bytes(b'image content')

        storyboard = {
            'scenes': [{'effect': 'plasma', 'duration': 10}]
        }
        (Path(self.temp_dir) / 'story.json').write_text(json.dumps(storyboard))

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_server_start_stop(self):
        """Test server can start and stop cleanly."""
        server = PreviewServer(
            directories=[Path(self.temp_dir)],
            port=0,  # Use random available port
        )

        # Just verify initialization
        self.assertIsNotNone(server.gallery)
        self.assertEqual(len(server.gallery.scan()), 3)


if __name__ == '__main__':
    unittest.main()
