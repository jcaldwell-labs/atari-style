"""Gallery module for scanning and managing media files.

Scans directories for supported media types and extracts metadata
for display in the preview server.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def format_bytes(size_bytes: int) -> str:
    """Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable string (e.g., "1.5 MB")
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@dataclass
class MediaFile:
    """Represents a media file with metadata."""

    path: Path
    filename: str
    file_type: str  # 'video', 'image', 'storyboard', 'input_script'
    extension: str
    size_bytes: int
    modified_time: datetime

    # Relative path from scan root for unique identification
    relative_path: str = ""

    # Optional metadata (populated by probing)
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None

    # Storyboard-specific metadata
    storyboard_data: Optional[Dict] = field(default=None, repr=False)

    @property
    def size_human(self) -> str:
        """Return human-readable file size."""
        return format_bytes(self.size_bytes)

    @property
    def modified_human(self) -> str:
        """Return human-readable modification time."""
        return self.modified_time.strftime("%Y-%m-%d %H:%M")

    @property
    def duration_human(self) -> str:
        """Return human-readable duration."""
        if self.duration is None:
            return "-"
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        if minutes > 0:
            return f"{minutes}:{seconds:02d}"
        return f"{seconds}s"

    @property
    def resolution(self) -> str:
        """Return resolution string."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "-"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for this file.

        Uses relative_path if available, otherwise filename.
        This handles duplicate filenames in subdirectories.
        """
        return self.relative_path if self.relative_path else self.filename

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'path': str(self.path),
            'filename': self.filename,
            'relative_path': self.relative_path,
            'unique_id': self.unique_id,
            'file_type': self.file_type,
            'extension': self.extension,
            'size_bytes': self.size_bytes,
            'size_human': self.size_human,
            'modified_time': self.modified_time.isoformat(),
            'modified_human': self.modified_human,
            'duration': self.duration,
            'duration_human': self.duration_human,
            'width': self.width,
            'height': self.height,
            'resolution': self.resolution,
            'fps': self.fps,
        }


class Gallery:
    """Scans directories and manages media file collections."""

    # Supported file extensions by type
    EXTENSIONS = {
        'video': {'.mp4', '.webm', '.avi', '.mov', '.mkv'},
        'image': {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'},
        'storyboard': {'.json'},  # Will check content to differentiate
    }

    def __init__(self, directories: Optional[List[Path]] = None, cache_ttl: float = 30.0):
        """Initialize gallery with directories to scan.

        Args:
            directories: List of directories to scan. Defaults to ['output/']
            cache_ttl: Cache time-to-live in seconds. Set to 0 to disable caching.
        """
        if directories is None:
            # Default to output directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            directories = [project_root / 'output']

        self.directories = [Path(d) for d in directories]
        self.files: List[MediaFile] = []
        self._ffprobe_available: Optional[bool] = None
        self._cache_ttl = cache_ttl
        self._last_scan_time: float = 0
        # Track files by unique_id for lookup
        self._file_index: Dict[str, MediaFile] = {}

    def _check_ffprobe(self) -> bool:
        """Check if ffprobe is available."""
        if self._ffprobe_available is None:
            try:
                subprocess.run(
                    ['ffprobe', '-version'],
                    capture_output=True,
                    check=True
                )
                self._ffprobe_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._ffprobe_available = False
        return self._ffprobe_available

    def _get_file_type(self, path: Path) -> Optional[str]:
        """Determine file type from extension and content."""
        ext = path.suffix.lower()

        # Check video extensions
        if ext in self.EXTENSIONS['video']:
            return 'video'

        # Check image extensions
        if ext in self.EXTENSIONS['image']:
            return 'image'

        # JSON files need content inspection
        if ext == '.json':
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                # Check for storyboard markers
                if 'scenes' in data or 'timeline' in data:
                    return 'storyboard'

                # Check for input script markers
                if 'keyframes' in data and 'duration' in data:
                    return 'input_script'

                # Generic JSON - treat as storyboard
                return 'storyboard'

            except (json.JSONDecodeError, IOError):
                return None

        return None

    def _probe_video(self, path: Path) -> Dict:
        """Probe video file for metadata using ffprobe."""
        if not self._check_ffprobe():
            return {}

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    str(path)
                ],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            metadata = {}

            # Get duration from format
            if 'format' in data and 'duration' in data['format']:
                metadata['duration'] = float(data['format']['duration'])

            # Get video stream info
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    metadata['width'] = stream.get('width')
                    metadata['height'] = stream.get('height')

                    # Parse frame rate (can be "30/1" or "29.97")
                    fps_str = stream.get('r_frame_rate', '')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        if int(den) != 0:
                            metadata['fps'] = round(int(num) / int(den), 2)
                    elif fps_str:
                        metadata['fps'] = float(fps_str)
                    break

            return metadata

        except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
            return {}

    def _probe_image(self, path: Path) -> Dict:
        """Probe image file for dimensions using ffprobe."""
        if not self._check_ffprobe():
            return {}

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_streams',
                    str(path)
                ],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)

            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':  # Images are treated as video streams
                    return {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                    }

            return {}

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    def _parse_storyboard(self, path: Path) -> Dict:
        """Parse storyboard JSON for metadata."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)

            metadata = {'storyboard_data': data}

            # Extract duration if available
            if 'duration' in data:
                metadata['duration'] = float(data['duration'])
            elif 'scenes' in data:
                # Calculate total duration from scenes
                total = sum(
                    scene.get('duration', 0)
                    for scene in data['scenes']
                )
                if total > 0:
                    metadata['duration'] = total

            # Extract resolution if specified
            if 'width' in data:
                metadata['width'] = data['width']
            if 'height' in data:
                metadata['height'] = data['height']

            return metadata

        except (json.JSONDecodeError, IOError):
            return {}

    def scan(self, recursive: bool = True, force: bool = False) -> List[MediaFile]:
        """Scan directories for media files.

        Args:
            recursive: Whether to scan subdirectories
            force: Force rescan even if cache is still valid

        Returns:
            List of MediaFile objects
        """
        # Check if cache is still valid
        if not force and self._cache_ttl > 0 and self.files:
            elapsed = time.time() - self._last_scan_time
            if elapsed < self._cache_ttl:
                return self.files

        self.files = []
        self._file_index = {}

        for directory in self.directories:
            if not directory.exists():
                continue

            # Get all files
            if recursive:
                paths = directory.rglob('*')
            else:
                paths = directory.glob('*')

            for path in paths:
                if not path.is_file():
                    continue

                file_type = self._get_file_type(path)
                if file_type is None:
                    continue

                # Get basic file info
                stat = path.stat()

                # Calculate relative path from directory root
                try:
                    relative_path = str(path.relative_to(directory))
                except ValueError:
                    relative_path = path.name

                media_file = MediaFile(
                    path=path,
                    filename=path.name,
                    relative_path=relative_path,
                    file_type=file_type,
                    extension=path.suffix.lower(),
                    size_bytes=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                )

                # Probe for additional metadata
                if file_type == 'video':
                    metadata = self._probe_video(path)
                elif file_type == 'image':
                    metadata = self._probe_image(path)
                elif file_type in ('storyboard', 'input_script'):
                    metadata = self._parse_storyboard(path)
                else:
                    metadata = {}

                # Apply metadata
                for key, value in metadata.items():
                    if hasattr(media_file, key):
                        setattr(media_file, key, value)

                self.files.append(media_file)
                self._file_index[media_file.unique_id] = media_file

        # Sort by modification time (newest first)
        self.files.sort(key=lambda f: f.modified_time, reverse=True)

        # Update cache timestamp
        self._last_scan_time = time.time()

        return self.files

    def filter_by_type(self, file_type: str) -> List[MediaFile]:
        """Get files of a specific type.

        Args:
            file_type: One of 'video', 'image', 'storyboard', 'input_script'

        Returns:
            Filtered list of MediaFile objects
        """
        return [f for f in self.files if f.file_type == file_type]

    def get_by_filename(self, filename: str) -> Optional[MediaFile]:
        """Get a file by its filename.

        Note: For files with duplicate names in subdirectories,
        use get_by_id() with the relative_path instead.

        Args:
            filename: Name of the file

        Returns:
            MediaFile if found, None otherwise
        """
        for f in self.files:
            if f.filename == filename:
                return f
        return None

    def get_by_id(self, unique_id: str) -> Optional[MediaFile]:
        """Get a file by its unique identifier.

        This handles duplicate filenames by using relative paths.

        Args:
            unique_id: The unique_id (relative_path or filename) of the file

        Returns:
            MediaFile if found, None otherwise
        """
        return self._file_index.get(unique_id)

    def get_summary(self) -> Dict:
        """Get summary statistics about the gallery.

        Returns:
            Dictionary with counts and totals
        """
        total_size = sum(f.size_bytes for f in self.files)

        summary = {
            'total_files': len(self.files),
            'total_size': total_size,
            'total_size_human': format_bytes(total_size),
            'by_type': {},
        }

        for file_type in ['video', 'image', 'storyboard', 'input_script']:
            files = self.filter_by_type(file_type)
            type_size = sum(f.size_bytes for f in files)
            summary['by_type'][file_type] = {
                'count': len(files),
                'size': type_size,
                'size_human': format_bytes(type_size),
            }

        return summary
