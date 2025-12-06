"""Tests for chapter markers CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from atari_style.tools.chapter_markers import (
    load_script,
    format_timestamp,
    get_segment_label,
    extract_chapters,
    format_chapters_text,
    format_chapters_json,
    main,
    Chapter,
    HOUR_THRESHOLD_SECONDS,
)
from atari_style.core.video_script import (
    VideoScript,
    TitleSegment,
    VisualizationSegment,
    SweepSegment,
    TransitionSegment,
    PauseSegment,
    SegmentType,
)


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
            {"type": "title", "duration": 3.0, "text": "Introduction"},
            {"type": "visualization", "duration": 12.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 2.0, "text": "Part Two"},
            {"type": "sweep", "duration": 28.0, "visualizer": "test", "from": {}, "to": {}},
            {"type": "title", "duration": 2.0, "text": "Conclusion"},
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
        assert script.segment_count == 5

    def test_load_missing_file(self, tmp_path):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_script(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_script(str(bad_file))


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_zero_seconds(self):
        """Test formatting 0 seconds."""
        assert format_timestamp(0) == "0:00"

    def test_under_minute(self):
        """Test formatting seconds under a minute."""
        assert format_timestamp(45) == "0:45"

    def test_exact_minute(self):
        """Test formatting exactly 1 minute."""
        assert format_timestamp(60) == "1:00"

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        assert format_timestamp(90) == "1:30"
        assert format_timestamp(125) == "2:05"

    def test_over_hour_automatic(self):
        """Test that hours format is used when >= 1 hour."""
        assert format_timestamp(3600) == "1:00:00"
        assert format_timestamp(3661) == "1:01:01"
        assert format_timestamp(7325) == "2:02:05"

    def test_force_hours_format(self):
        """Test forcing hours format for short durations."""
        assert format_timestamp(90, use_hours=True) == "0:01:30"
        assert format_timestamp(0, use_hours=True) == "0:00:00"

    def test_fractional_seconds(self):
        """Test that fractional seconds are truncated."""
        assert format_timestamp(45.7) == "0:45"
        assert format_timestamp(89.9) == "1:29"


class TestGetSegmentLabel:
    """Tests for get_segment_label function."""

    def test_title_segment(self):
        """Test label for title segment."""
        segment = TitleSegment(duration=3.0, text="Hello World")
        assert get_segment_label(segment) == "Hello World"

    def test_visualization_segment(self):
        """Test label for visualization segment."""
        segment = VisualizationSegment(duration=10.0, visualizer="lissajous")
        assert get_segment_label(segment) == "Visualization: lissajous"

    def test_sweep_segment(self):
        """Test label for sweep segment."""
        segment = SweepSegment(
            duration=8.0,
            visualizer="plasma",
            from_params={},
            to_params={}
        )
        assert get_segment_label(segment) == "Parameter Sweep: plasma"

    def test_transition_segment(self):
        """Test label for transition segment."""
        segment = TransitionSegment(duration=1.0, effect="fade")
        assert get_segment_label(segment) == "Transition: fade"

    def test_pause_segment(self):
        """Test label for pause segment."""
        segment = PauseSegment(duration=2.0)
        assert get_segment_label(segment) == "Pause"


class TestExtractChapters:
    """Tests for extract_chapters function."""

    def test_extract_title_segments_only(self, tmp_path):
        """Test extracting only title segments (default behavior)."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        chapters = extract_chapters(script)

        assert len(chapters) == 3
        assert chapters[0].timestamp == 0.0
        assert chapters[0].label == "Introduction"
        assert chapters[1].timestamp == 15.0  # 3 + 12
        assert chapters[1].label == "Part Two"
        assert chapters[2].timestamp == 45.0  # 3 + 12 + 2 + 28
        assert chapters[2].label == "Conclusion"

    def test_extract_all_segments(self, tmp_path):
        """Test extracting all segments with include_all flag."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))

        chapters = extract_chapters(script, include_all=True)

        assert len(chapters) == 5
        assert chapters[0].label == "Introduction"
        assert chapters[1].label == "Visualization: test"
        assert chapters[2].label == "Part Two"
        assert chapters[3].label == "Parameter Sweep: test"
        assert chapters[4].label == "Conclusion"

    def test_empty_script(self):
        """Test with empty script (no segments)."""
        script = VideoScript(name="empty", segments=[])

        chapters = extract_chapters(script)

        assert len(chapters) == 0

    def test_no_title_segments(self, tmp_path):
        """Test script with no title segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}},
        ])
        script = load_script(str(script_path))

        chapters = extract_chapters(script)

        assert len(chapters) == 0

    def test_cumulative_timestamps(self, tmp_path):
        """Test that timestamps are cumulative."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 5.0, "text": "First"},
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 3.0, "text": "Second"},
            {"type": "visualization", "duration": 20.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 2.0, "text": "Third"},
        ])
        script = load_script(str(script_path))

        chapters = extract_chapters(script)

        assert len(chapters) == 3
        assert chapters[0].timestamp == 0.0
        assert chapters[1].timestamp == 15.0  # 5 + 10
        assert chapters[2].timestamp == 38.0  # 5 + 10 + 3 + 20


class TestFormatChaptersText:
    """Tests for format_chapters_text function."""

    def test_format_basic(self):
        """Test basic text formatting."""
        chapters = [
            Chapter(timestamp=0, label="Introduction"),
            Chapter(timestamp=15, label="Main Content"),
            Chapter(timestamp=90, label="Conclusion"),
        ]

        output = format_chapters_text(chapters, total_duration=100)

        lines = output.strip().split('\n')
        assert len(lines) == 3
        assert lines[0] == "0:00 Introduction"
        assert lines[1] == "0:15 Main Content"
        assert lines[2] == "1:30 Conclusion"

    def test_format_empty(self):
        """Test formatting empty chapters list."""
        output = format_chapters_text([], total_duration=100)
        assert output == ""

    def test_format_uses_hours_for_long_videos(self):
        """Test that hours format is used for videos >= 1 hour."""
        chapters = [
            Chapter(timestamp=0, label="Start"),
            Chapter(timestamp=3700, label="End"),
        ]

        output = format_chapters_text(chapters, total_duration=4000)

        lines = output.strip().split('\n')
        assert "0:00:00 Start" in lines[0]
        assert "1:01:40 End" in lines[1]

    def test_format_uses_minutes_for_short_videos(self):
        """Test that M:SS format is used for videos under 1 hour."""
        chapters = [
            Chapter(timestamp=0, label="Start"),
            Chapter(timestamp=1800, label="End"),
        ]

        output = format_chapters_text(chapters, total_duration=2000)

        lines = output.strip().split('\n')
        assert "0:00 Start" in lines[0]
        assert "30:00 End" in lines[1]


class TestFormatChaptersJson:
    """Tests for format_chapters_json function."""

    def test_format_basic(self):
        """Test basic JSON formatting."""
        chapters = [
            Chapter(timestamp=0, label="Introduction"),
            Chapter(timestamp=15.5, label="Main Content"),
        ]

        output = format_chapters_json(chapters)
        data = json.loads(output)

        assert "chapters" in data
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["timestamp"] == 0
        assert data["chapters"][0]["label"] == "Introduction"
        assert data["chapters"][1]["timestamp"] == 15  # Truncated to int
        assert data["chapters"][1]["label"] == "Main Content"

    def test_format_empty(self):
        """Test formatting empty chapters list."""
        output = format_chapters_json([])
        data = json.loads(output)

        assert data == {"chapters": []}


class TestMain:
    """Tests for main CLI entry point."""

    def test_valid_text_output(self, tmp_path, monkeypatch, capsys):
        """Test valid text output through main."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path)
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "0:00 Introduction" in captured.out
        assert "0:15 Part Two" in captured.out

    def test_valid_json_output(self, tmp_path, monkeypatch, capsys):
        """Test valid JSON output through main."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path), '--json'
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "chapters" in data
        assert len(data["chapters"]) == 3

    def test_output_to_file(self, tmp_path, monkeypatch):
        """Test writing output to file."""
        script_path = create_test_script(tmp_path)
        output_file = tmp_path / "output" / "chapters.txt"
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path),
            '-o', str(output_file)
        ])

        result = main()

        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "0:00 Introduction" in content

    def test_include_all_flag(self, tmp_path, monkeypatch, capsys):
        """Test --include-all flag."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path), '--include-all'
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Visualization: test" in captured.out
        assert "Parameter Sweep: test" in captured.out

    def test_missing_input_file(self, tmp_path, monkeypatch):
        """Test error for missing input file."""
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(tmp_path / "nonexistent.json")
        ])

        result = main()

        assert result == 1

    def test_invalid_json(self, tmp_path, monkeypatch):
        """Test error for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid }")

        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(bad_file)
        ])

        result = main()

        assert result == 1

    def test_verbose_quiet_mutual_exclusion(self, tmp_path, monkeypatch):
        """Test that verbose and quiet flags are mutually exclusive."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path), '-v', '-q'
        ])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    def test_verbose_output(self, tmp_path, monkeypatch, capsys):
        """Test verbose output shows extra info."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'chapter-markers', str(script_path), '-v'
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Loading script:" in captured.err
        assert "Script:" in captured.err
        assert "Chapters found:" in captured.err


class TestCLIIntegration:
    """Integration tests running CLI as subprocess."""

    def test_cli_help(self):
        """Test CLI --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'chapter' in result.stdout.lower()
        assert 'output' in result.stdout.lower()

    def test_cli_text_output(self, tmp_path):
        """Test CLI text output end-to-end."""
        script_path = create_test_script(tmp_path)

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "0:00 Introduction" in result.stdout

    def test_cli_json_output(self, tmp_path):
        """Test CLI JSON output end-to-end."""
        script_path = create_test_script(tmp_path)

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(script_path), '--json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "chapters" in data

    def test_cli_stdin_input(self, tmp_path):
        """Test reading script from stdin."""
        script = {
            "name": "stdin-test",
            "format": "preview",
            "segments": [
                {"type": "title", "duration": 3.0, "text": "Stdin Test"},
                {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}}
            ]
        }

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers', '-'],
            input=json.dumps(script),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "0:00 Stdin Test" in result.stdout

    def test_cli_output_to_file(self, tmp_path):
        """Test CLI output to file."""
        script_path = create_test_script(tmp_path)
        output_file = tmp_path / "chapters.txt"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(script_path), '-o', str(output_file), '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "0:00 Introduction" in content

    def test_cli_example_script(self):
        """Test CLI with example script from repository."""
        example_path = Path(__file__).parent.parent / 'scripts' / 'videos' / 'lissajous-intro.json'
        if not example_path.exists():
            pytest.skip("Example script not found")

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(example_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Lissajous Curves" in result.stdout

    def test_cli_missing_file(self, tmp_path):
        """Test CLI error for missing file."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(tmp_path / "nonexistent.json")],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_cli_invalid_json(self, tmp_path):
        """Test CLI error for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid }")

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.chapter_markers',
             str(bad_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "Error" in result.stderr


class TestHourThreshold:
    """Tests for hour threshold constant and behavior."""

    def test_hour_threshold_value(self):
        """Test that hour threshold is 3600 seconds."""
        assert HOUR_THRESHOLD_SECONDS == 3600

    def test_just_under_hour(self):
        """Test formatting just under 1 hour."""
        output = format_chapters_text(
            [Chapter(timestamp=3599, label="Almost Hour")],
            total_duration=3599
        )
        # Should use M:SS format
        assert "59:59 Almost Hour" in output

    def test_exactly_hour(self):
        """Test formatting exactly 1 hour."""
        output = format_chapters_text(
            [Chapter(timestamp=0, label="Start")],
            total_duration=3600
        )
        # Should use H:MM:SS format
        assert "0:00:00 Start" in output
