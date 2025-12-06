"""Tests for thumbnail extractor CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

from atari_style.tools.thumbnail_extractor import (
    load_script,
    select_evenly_spaced_frames,
    select_title_card_frames,
    select_frames,
    extract_thumbnails,
    get_segment_start_times,
    main,
    THUMBNAIL_WIDTH,
    THUMBNAIL_HEIGHT,
)
from atari_style.core.video_script import VideoScript


class MockArgs:
    """Mock argparse.Namespace for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def create_test_script(tmp_path: Path, segments: list = None) -> Path:
    """Create a test video script file.

    Args:
        tmp_path: Temporary directory
        segments: List of segment definitions (uses default if None)

    Returns:
        Path to created script file
    """
    if segments is None:
        segments = [
            {"type": "title", "duration": 3.0, "text": "Hello World"},
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 2.0, "text": "Part Two"},
            {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}},
        ]

    script = {
        "name": "test-script",
        "version": "1.0",
        "format": "youtube_landscape",
        "segments": segments
    }
    script_path = tmp_path / "test.json"
    script_path.write_text(json.dumps(script))
    return script_path


class TestLoadScript:
    """Tests for load_script function."""

    def test_load_from_file(self, tmp_path):
        """Test loading script from file."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        assert script.name == "test-script"
        assert script.segment_count == 4

    def test_load_missing_file(self, tmp_path):
        """Test loading non-existent file."""
        import pytest
        with pytest.raises(FileNotFoundError):
            load_script(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        import pytest
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_script(str(bad_file))


class TestGetSegmentStartTimes:
    """Tests for get_segment_start_times function."""

    def test_single_segment(self, tmp_path):
        """Test with single segment."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 5.0, "text": "Only One"}
        ])
        script = load_script(str(script_path))

        start_times = get_segment_start_times(script)

        assert start_times == [0.0]

    def test_multiple_segments(self, tmp_path):
        """Test with multiple segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "First"},
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 2.0, "text": "Second"},
        ])
        script = load_script(str(script_path))

        start_times = get_segment_start_times(script)

        assert len(start_times) == 3
        assert start_times[0] == 0.0
        assert start_times[1] == 3.0
        assert start_times[2] == 13.0


class TestSelectEvenlySpacedFrames:
    """Tests for select_evenly_spaced_frames function."""

    def test_select_three_frames(self, tmp_path):
        """Test selecting 3 evenly spaced frames."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_evenly_spaced_frames(script, 3)

        assert len(frames) == 3
        # Frames should be distributed across the video
        assert frames[0].timestamp < frames[1].timestamp < frames[2].timestamp

    def test_select_single_frame(self, tmp_path):
        """Test selecting 1 frame."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_evenly_spaced_frames(script, 1)

        assert len(frames) == 1
        # Single frame should be in the middle
        total_duration = script.total_duration
        assert 0.3 * total_duration < frames[0].timestamp < 0.7 * total_duration

    def test_select_zero_frames(self, tmp_path):
        """Test selecting 0 frames."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_evenly_spaced_frames(script, 0)

        assert len(frames) == 0

    def test_empty_script(self, tmp_path):
        """Test with empty script (no segments)."""
        script = VideoScript(
            name="empty",
            segments=[],
        )

        frames = select_evenly_spaced_frames(script, 3)

        assert len(frames) == 0


class TestSelectTitleCardFrames:
    """Tests for select_title_card_frames function."""

    def test_select_title_frames(self, tmp_path):
        """Test selecting title card frames."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_title_card_frames(script)

        assert len(frames) == 2  # Two title segments in test script
        assert all(f.segment_type == 'title' for f in frames)

    def test_no_title_segments(self, tmp_path):
        """Test script with no title segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}},
        ])
        script = load_script(str(script_path))

        frames = select_title_card_frames(script)

        assert len(frames) == 0

    def test_only_title_segments(self, tmp_path):
        """Test script with only title segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "First"},
            {"type": "title", "duration": 2.0, "text": "Second"},
            {"type": "title", "duration": 4.0, "text": "Third"},
        ])
        script = load_script(str(script_path))

        frames = select_title_card_frames(script)

        assert len(frames) == 3


class TestSelectFrames:
    """Tests for select_frames function."""

    def test_evenly_spaced_strategy(self, tmp_path):
        """Test evenly_spaced strategy."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_frames(script, 'evenly_spaced', 3)

        assert len(frames) == 3

    def test_title_strategy(self, tmp_path):
        """Test title strategy."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        frames = select_frames(script, 'title', 0)  # count ignored for title

        assert len(frames) == 2


class TestExtractThumbnails:
    """Tests for extract_thumbnails function."""

    def test_extract_evenly_spaced(self, tmp_path):
        """Test extracting evenly spaced thumbnails."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        output_dir = tmp_path / "output"

        metadata = extract_thumbnails(
            script=script,
            output_dir=output_dir,
            strategy='evenly_spaced',
            count=2,
            quiet=True
        )

        assert len(metadata) == 2
        # Check output files exist
        for meta in metadata:
            assert (output_dir / meta['filename']).exists()

    def test_extract_title_frames(self, tmp_path):
        """Test extracting title card thumbnails."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        output_dir = tmp_path / "output"

        metadata = extract_thumbnails(
            script=script,
            output_dir=output_dir,
            strategy='title',
            count=0,
            quiet=True
        )

        assert len(metadata) == 2  # Two title segments
        for meta in metadata:
            assert meta['segment_type'] == 'title'

    def test_thumbnail_dimensions(self, tmp_path):
        """Test thumbnail dimensions are correct."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        output_dir = tmp_path / "output"

        metadata = extract_thumbnails(
            script=script,
            output_dir=output_dir,
            strategy='evenly_spaced',
            count=1,
            quiet=True
        )

        assert len(metadata) == 1
        assert metadata[0]['width'] == THUMBNAIL_WIDTH
        assert metadata[0]['height'] == THUMBNAIL_HEIGHT

    def test_creates_output_directory(self, tmp_path):
        """Test that output directory is created if missing."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        output_dir = tmp_path / "nested" / "path" / "output"

        assert not output_dir.exists()

        extract_thumbnails(
            script=script,
            output_dir=output_dir,
            strategy='evenly_spaced',
            count=1,
            quiet=True
        )

        assert output_dir.exists()


class TestMain:
    """Tests for main CLI entry point."""

    def test_missing_output(self, tmp_path, monkeypatch, capsys):
        """Test error when output not specified."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'thumbnail-extractor', str(script_path)
        ])

        # Should exit with error (argparse handles required arg)
        import pytest
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    def test_valid_extraction(self, tmp_path, monkeypatch):
        """Test valid extraction through main."""
        script_path = create_test_script(tmp_path)
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, 'argv', [
            'thumbnail-extractor', str(script_path),
            '-o', str(output_dir),
            '-c', '2',
            '-q'
        ])

        result = main()

        assert result == 0
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.png"))) == 2

    def test_missing_input_file(self, tmp_path, monkeypatch):
        """Test error for missing input file."""
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, 'argv', [
            'thumbnail-extractor', str(tmp_path / "nonexistent.json"),
            '-o', str(output_dir)
        ])

        result = main()

        assert result == 1

    def test_invalid_json(self, tmp_path, monkeypatch):
        """Test error for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid }")
        output_dir = tmp_path / "output"

        monkeypatch.setattr(sys, 'argv', [
            'thumbnail-extractor', str(bad_file),
            '-o', str(output_dir)
        ])

        result = main()

        assert result == 1

    def test_title_strategy(self, tmp_path, monkeypatch):
        """Test title strategy through main."""
        script_path = create_test_script(tmp_path)
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, 'argv', [
            'thumbnail-extractor', str(script_path),
            '-o', str(output_dir),
            '-s', 'title',
            '-q'
        ])

        result = main()

        assert result == 0
        assert len(list(output_dir.glob("*.png"))) == 2  # Two title segments


class TestCLIIntegration:
    """Integration tests running CLI as subprocess."""

    def test_cli_help(self):
        """Test CLI --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'thumbnail' in result.stdout.lower()
        assert 'output' in result.stdout.lower()

    def test_cli_extraction(self, tmp_path):
        """Test CLI extraction end-to-end."""
        script_path = create_test_script(tmp_path)
        output_dir = tmp_path / "cli_output"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor',
             str(script_path), '-o', str(output_dir), '-c', '2', '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.png"))) == 2

    def test_cli_stdin_input(self, tmp_path):
        """Test reading script from stdin."""
        script = {
            "name": "stdin-test",
            "format": "preview",
            "segments": [
                {"type": "title", "duration": 3.0, "text": "Test"},
                {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}}
            ]
        }
        output_dir = tmp_path / "stdin_output"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor',
             '-', '-o', str(output_dir), '-c', '1', '-q'],
            input=json.dumps(script),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.png"))) == 1

    def test_cli_json_output(self, tmp_path):
        """Test --json flag outputs to stdout."""
        script_path = create_test_script(tmp_path)
        output_dir = tmp_path / "json_output"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor',
             str(script_path), '-o', str(output_dir), '-c', '1', '-q', '--json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Parse JSON from stdout
        output_data = json.loads(result.stdout)
        assert 'script_name' in output_data
        assert 'frames' in output_data
        assert len(output_data['frames']) == 1

    def test_cli_invalid_strategy(self, tmp_path):
        """Test invalid strategy shows error."""
        script_path = create_test_script(tmp_path)
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor',
             str(script_path), '-o', str(output_dir), '-s', 'invalid'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 2  # argparse error

    def test_cli_example_script(self):
        """Test CLI with example script from repository."""
        example_path = Path(__file__).parent.parent / 'scripts' / 'videos' / 'lissajous-intro.json'
        if not example_path.exists():
            import pytest
            pytest.skip("Example script not found")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [sys.executable, '-m', 'atari_style.tools.thumbnail_extractor',
                 str(example_path), '-o', tmp_dir, '-c', '3', '-q'],
                capture_output=True,
                text=True,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )

            assert result.returncode == 0
            assert len(list(Path(tmp_dir).glob("*.png"))) == 3
