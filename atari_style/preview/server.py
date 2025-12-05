"""HTTP preview server for atari-style media files.

Serves a web-based gallery and viewer for exported videos, images,
and storyboard JSON files. Uses Python's built-in http.server.
"""

import argparse
import json
import mimetypes
import sys
import urllib.parse
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

from .gallery import Gallery, MediaFile


class PreviewHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the preview server."""

    def __init__(self, *args, gallery: Gallery, templates_dir: Path, **kwargs):
        self.gallery = gallery
        self.templates_dir = templates_dir
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Route requests
        if path == '/' or path == '/index.html':
            self._serve_gallery(query)
        elif path == '/view':
            self._serve_viewer(query)
        elif path == '/storyboard':
            self._serve_storyboard(query)
        elif path == '/api/files':
            self._serve_api_files(query)
        elif path == '/api/summary':
            self._serve_api_summary()
        elif path.startswith('/media/'):
            self._serve_media_file(path[7:])  # Strip '/media/'
        elif path.startswith('/static/'):
            self._serve_static(path[8:])  # Strip '/static/'
        else:
            self.send_error(404, "Not Found")

    def _send_html(self, content: str, status: int = 200):
        """Send HTML response."""
        encoded = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        content = json.dumps(data, indent=2)
        encoded = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _load_template(self, name: str) -> str:
        """Load an HTML template."""
        template_path = self.templates_dir / name
        if template_path.exists():
            return template_path.read_text()
        return f"<!-- Template {name} not found -->"

    def _render_file_card(self, f: MediaFile) -> str:
        """Render a file card for the gallery."""
        type_icons = {
            'video': '🎬',
            'image': '🖼️',
            'storyboard': '📋',
            'input_script': '🎮',
        }
        icon = type_icons.get(f.file_type, '📄')

        # Build preview/thumbnail
        if f.file_type == 'video':
            preview = f'''
                <div class="preview video-preview">
                    <video muted loop preload="metadata">
                        <source src="/media/{urllib.parse.quote(f.filename)}" type="video/mp4">
                    </video>
                    <div class="play-overlay">▶</div>
                </div>
            '''
        elif f.file_type == 'image':
            preview = f'''
                <div class="preview image-preview">
                    <img src="/media/{urllib.parse.quote(f.filename)}" alt="{f.filename}" loading="lazy">
                </div>
            '''
        else:
            preview = f'''
                <div class="preview icon-preview">
                    <span class="icon">{icon}</span>
                </div>
            '''

        # Build info section
        info_items = [f'<span class="size">{f.size_human}</span>']
        if f.duration:
            info_items.append(f'<span class="duration">{f.duration_human}</span>')
        if f.width and f.height:
            info_items.append(f'<span class="resolution">{f.resolution}</span>')

        view_url = f'/view?file={urllib.parse.quote(f.filename)}'
        if f.file_type == 'storyboard':
            view_url = f'/storyboard?file={urllib.parse.quote(f.filename)}'

        return f'''
            <div class="file-card" data-type="{f.file_type}">
                <a href="{view_url}">
                    {preview}
                    <div class="file-info">
                        <div class="filename" title="{f.filename}">{icon} {f.filename}</div>
                        <div class="meta">
                            {' '.join(info_items)}
                        </div>
                        <div class="modified">{f.modified_human}</div>
                    </div>
                </a>
            </div>
        '''

    def _serve_gallery(self, query: dict):
        """Serve the main gallery page."""
        # Refresh file list
        self.gallery.scan()

        # Filter by type if requested
        type_filter = query.get('type', [None])[0]
        if type_filter and type_filter != 'all':
            files = self.gallery.filter_by_type(type_filter)
        else:
            files = self.gallery.files

        summary = self.gallery.get_summary()

        # Render file cards
        if files:
            cards_html = '\n'.join(self._render_file_card(f) for f in files)
        else:
            cards_html = '''
                <div class="empty-state">
                    <span class="icon">📂</span>
                    <p>No media files found</p>
                    <p class="hint">Export some videos or images to the output/ directory</p>
                </div>
            '''

        # Build filter buttons
        filter_buttons = [
            ('all', 'All', len(self.gallery.files)),
            ('video', '🎬 Videos', summary['by_type']['video']['count']),
            ('image', '🖼️ Images', summary['by_type']['image']['count']),
            ('storyboard', '📋 Storyboards', summary['by_type']['storyboard']['count']),
            ('input_script', '🎮 Input Scripts', summary['by_type']['input_script']['count']),
        ]

        filter_html = ''
        for type_key, label, count in filter_buttons:
            if count == 0 and type_key != 'all':
                continue
            active = 'active' if (type_filter or 'all') == type_key else ''
            filter_html += f'''
                <a href="/?type={type_key}" class="filter-btn {active}">
                    {label} <span class="count">({count})</span>
                </a>
            '''

        # Build page
        template = self._load_template('index.html')
        html = template.replace('{{CARDS}}', cards_html)
        html = html.replace('{{FILTERS}}', filter_html)
        html = html.replace('{{TOTAL_FILES}}', str(summary['total_files']))
        html = html.replace('{{TOTAL_SIZE}}', summary['total_size_human'])

        self._send_html(html)

    def _serve_viewer(self, query: dict):
        """Serve the file viewer page."""
        filename = query.get('file', [None])[0]
        if not filename:
            self.send_error(400, "Missing file parameter")
            return

        media_file = self.gallery.get_by_filename(filename)
        if not media_file:
            self.send_error(404, "File not found")
            return

        # Build media element based on type
        if media_file.file_type == 'video':
            media_html = f'''
                <video controls autoplay loop class="media-content">
                    <source src="/media/{urllib.parse.quote(filename)}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
            '''
        elif media_file.file_type == 'image':
            media_html = f'''
                <img src="/media/{urllib.parse.quote(filename)}"
                     alt="{filename}" class="media-content">
            '''
        else:
            # JSON files - show formatted content
            try:
                with open(media_file.path, 'r') as f:
                    data = json.load(f)
                json_str = json.dumps(data, indent=2)
                media_html = f'<pre class="json-content">{json_str}</pre>'
            except (json.JSONDecodeError, IOError):
                media_html = '<p class="error">Error loading file</p>'

        # Build info panel
        info_html = f'''
            <div class="info-panel">
                <h2>{filename}</h2>
                <dl>
                    <dt>Type</dt><dd>{media_file.file_type}</dd>
                    <dt>Size</dt><dd>{media_file.size_human}</dd>
                    <dt>Modified</dt><dd>{media_file.modified_human}</dd>
        '''
        if media_file.duration:
            info_html += f'<dt>Duration</dt><dd>{media_file.duration_human}</dd>'
        if media_file.width and media_file.height:
            info_html += f'<dt>Resolution</dt><dd>{media_file.resolution}</dd>'
        if media_file.fps:
            info_html += f'<dt>Frame Rate</dt><dd>{media_file.fps} fps</dd>'
        info_html += '</dl></div>'

        template = self._load_template('viewer.html')
        html = template.replace('{{FILENAME}}', filename)
        html = html.replace('{{MEDIA}}', media_html)
        html = html.replace('{{INFO}}', info_html)

        self._send_html(html)

    def _serve_storyboard(self, query: dict):
        """Serve the storyboard timeline viewer."""
        filename = query.get('file', [None])[0]
        if not filename:
            self.send_error(400, "Missing file parameter")
            return

        media_file = self.gallery.get_by_filename(filename)
        if not media_file:
            self.send_error(404, "File not found")
            return

        # Load storyboard data
        try:
            with open(media_file.path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.send_error(500, "Error loading storyboard")
            return

        # Build timeline visualization
        timeline_html = self._render_timeline(data)

        # Build scene cards
        scenes_html = self._render_scenes(data)

        template = self._load_template('storyboard.html')
        html = template.replace('{{FILENAME}}', filename)
        html = html.replace('{{TIMELINE}}', timeline_html)
        html = html.replace('{{SCENES}}', scenes_html)
        html = html.replace('{{JSON}}', json.dumps(data, indent=2))

        self._send_html(html)

    def _render_timeline(self, data: dict) -> str:
        """Render storyboard timeline visualization."""
        scenes = data.get('scenes', [])
        if not scenes:
            return '<div class="timeline-empty">No scenes defined</div>'

        total_duration = sum(s.get('duration', 0) for s in scenes)
        if total_duration == 0:
            return '<div class="timeline-empty">No duration specified</div>'

        timeline_html = '<div class="timeline">'
        current_time = 0

        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

        for i, scene in enumerate(scenes):
            duration = scene.get('duration', 0)
            width_pct = (duration / total_duration) * 100
            color = colors[i % len(colors)]
            effect = scene.get('effect', scene.get('animation', 'unknown'))

            timeline_html += f'''
                <div class="timeline-segment"
                     style="width: {width_pct}%; background-color: {color};"
                     title="{effect}: {duration}s">
                    <span class="segment-label">{effect}</span>
                </div>
            '''
            current_time += duration

        timeline_html += '</div>'
        timeline_html += f'<div class="timeline-duration">Total: {total_duration}s</div>'

        return timeline_html

    def _render_scenes(self, data: dict) -> str:
        """Render storyboard scene cards."""
        scenes = data.get('scenes', [])
        if not scenes:
            return '<p class="empty">No scenes defined</p>'

        html = '<div class="scene-grid">'
        current_time = 0

        for i, scene in enumerate(scenes):
            duration = scene.get('duration', 0)
            effect = scene.get('effect', scene.get('animation', 'unknown'))
            params = scene.get('params', scene.get('parameters', {}))

            # Format parameters
            params_html = ''
            if params:
                for key, value in params.items():
                    params_html += f'<div class="param"><span>{key}:</span> {value}</div>'

            html += f'''
                <div class="scene-card">
                    <div class="scene-header">
                        <span class="scene-num">Scene {i + 1}</span>
                        <span class="scene-time">{current_time}s - {current_time + duration}s</span>
                    </div>
                    <div class="scene-effect">{effect}</div>
                    <div class="scene-duration">{duration}s</div>
                    <div class="scene-params">{params_html or '<em>No parameters</em>'}</div>
                </div>
            '''
            current_time += duration

        html += '</div>'
        return html

    def _serve_media_file(self, filename: str):
        """Serve a media file directly."""
        filename = urllib.parse.unquote(filename)
        media_file = self.gallery.get_by_filename(filename)

        if not media_file:
            self.send_error(404, "File not found")
            return

        # Serve the file
        try:
            with open(media_file.path, 'rb') as f:
                content = f.read()

            # Determine content type
            content_type, _ = mimetypes.guess_type(str(media_file.path))
            if not content_type:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'max-age=3600')
            self.end_headers()
            self.wfile.write(content)

        except IOError:
            self.send_error(500, "Error reading file")

    def _serve_static(self, path: str):
        """Serve static files (CSS, JS)."""
        static_path = self.templates_dir / 'static' / path

        if not static_path.exists() or not static_path.is_file():
            self.send_error(404, "Static file not found")
            return

        try:
            with open(static_path, 'rb') as f:
                content = f.read()

            content_type, _ = mimetypes.guess_type(str(static_path))
            if not content_type:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        except IOError:
            self.send_error(500, "Error reading file")

    def _serve_api_files(self, query: dict):
        """Serve file list as JSON."""
        self.gallery.scan()

        type_filter = query.get('type', [None])[0]
        if type_filter and type_filter != 'all':
            files = self.gallery.filter_by_type(type_filter)
        else:
            files = self.gallery.files

        self._send_json({
            'files': [f.to_dict() for f in files],
            'count': len(files),
        })

    def _serve_api_summary(self):
        """Serve gallery summary as JSON."""
        self.gallery.scan()
        self._send_json(self.gallery.get_summary())

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[preview] {args[0]}")


class PreviewServer:
    """Preview server wrapper class."""

    def __init__(
        self,
        directories: Optional[list] = None,
        port: int = 8000,
        host: str = 'localhost'
    ):
        """Initialize the preview server.

        Args:
            directories: List of directories to scan for media
            port: HTTP port to listen on
            host: Host to bind to
        """
        self.port = port
        self.host = host
        self.gallery = Gallery(directories)
        self.templates_dir = Path(__file__).parent / 'templates'

    def run(self):
        """Start the server."""
        # Initial scan
        self.gallery.scan()
        summary = self.gallery.get_summary()

        title = "Atari-Style Preview Server"
        print(title)
        print("=" * len(title))
        print(f"Scanning: {', '.join(str(d) for d in self.gallery.directories)}")
        print(f"Found: {summary['total_files']} files ({summary['total_size_human']})")
        print(f"  Videos: {summary['by_type']['video']['count']}")
        print(f"  Images: {summary['by_type']['image']['count']}")
        print(f"  Storyboards: {summary['by_type']['storyboard']['count']}")
        print(f"  Input Scripts: {summary['by_type']['input_script']['count']}")
        print()
        print(f"Server running at http://{self.host}:{self.port}/")
        print("Press Ctrl+C to stop")
        print()

        # Create handler with gallery reference
        handler = partial(
            PreviewHandler,
            gallery=self.gallery,
            templates_dir=self.templates_dir,
        )

        try:
            server = HTTPServer((self.host, self.port), handler)
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Preview server for atari-style media files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Serve from default output/ directory
  %(prog)s -d ./renders             # Serve from custom directory
  %(prog)s -p 3000                  # Use custom port
  %(prog)s -d output -d storyboards # Multiple directories
"""
    )

    parser.add_argument(
        '-d', '--directory',
        action='append',
        dest='directories',
        help='Directory to scan for media files (can be repeated)'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8000,
        help='Port to run server on (default: 8000)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Host to bind to (default: localhost)'
    )

    args = parser.parse_args()

    # Convert directory strings to Paths
    directories = None
    if args.directories:
        directories = [Path(d) for d in args.directories]

    try:
        server = PreviewServer(
            directories=directories,
            port=args.port,
            host=args.host,
        )
        server.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
