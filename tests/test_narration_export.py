"""Tests for narration export CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

from atari_style.tools.narration_export import (
    load_script,
    generate_markers,
    format_json_output,
    format_markdown_output,
    format_time_display,
    NarrationMarker,
    main,
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
            {"type": "visualization", "duration": 10.0, "visualizer": "lissajous", "params": {"a": 1, "b": 2}},
            {"type": "title", "duration": 2.0, "text": "Part Two"},
            {"type": "sweep", "duration": 5.0, "visualizer": "plasma", "from": {"x": 0}, "to": {"x": 1}},
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


class TestFormatTimeDisplay:
    """Tests for format_time_display function."""

    def test_zero_seconds(self):
        """Test formatting zero seconds."""
        assert format_time_display(0.0) == "0:00"

    def test_under_minute(self):
        """Test formatting under 60 seconds."""
        assert format_time_display(3.0) == "0:03"
        assert format_time_display(45.5) == "0:45"

    def test_over_minute(self):
        """Test formatting over 60 seconds."""
        assert format_time_display(65.0) == "1:05"
        assert format_time_display(125.0) == "2:05"

    def test_exact_minute(self):
        """Test formatting exact minutes."""
        assert format_time_display(60.0) == "1:00"
        assert format_time_display(120.0) == "2:00"


class TestGenerateMarkers:
    """Tests for generate_markers function."""

    def test_title_segment_marker(self, tmp_path):
        """Test marker generation for title segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "Hello World"}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].time == 0.0
        assert markers[0].event == "title_card"
        assert markers[0].segment_type == "title"
        assert markers[0].cue == "Hello World"

    def test_visualization_segment_marker(self, tmp_path):
        """Test marker generation for visualization segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "visualization", "duration": 10.0, "visualizer": "lissajous", "params": {"a": 1, "b": 2}}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].time == 0.0
        assert markers[0].event == "visualization_start"
        assert markers[0].segment_type == "visualization"
        assert "lissajous" in markers[0].cue
        assert "a=1" in markers[0].cue
        assert "b=2" in markers[0].cue

    def test_visualization_no_params(self, tmp_path):
        """Test visualization with no params."""
        script_path = create_test_script(tmp_path, [
            {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].cue == "Visualizer: test"

    def test_sweep_segment_marker(self, tmp_path):
        """Test marker generation for sweep segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "sweep", "duration": 8.0, "visualizer": "plasma", "from": {"x": 0, "y": 0}, "to": {"x": 1, "y": 1}}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].event == "sweep_start"
        assert markers[0].segment_type == "sweep"
        assert "plasma" in markers[0].cue
        assert "from" in markers[0].cue
        assert "to" in markers[0].cue

    def test_transition_segment_marker(self, tmp_path):
        """Test marker generation for transition segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "transition", "duration": 1.0, "effect": "fade"}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].event == "transition"
        assert markers[0].segment_type == "transition"
        assert "fade" in markers[0].cue

    def test_pause_segment_marker(self, tmp_path):
        """Test marker generation for pause segments."""
        script_path = create_test_script(tmp_path, [
            {"type": "pause", "duration": 2.0}
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 1
        assert markers[0].event == "pause"
        assert markers[0].segment_type == "pause"
        assert "2.0" in markers[0].cue

    def test_marker_times_cumulative(self, tmp_path):
        """Test that marker times are cumulative."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "First"},
            {"type": "visualization", "duration": 10.0, "visualizer": "test", "params": {}},
            {"type": "title", "duration": 2.0, "text": "Second"},
        ])
        script = load_script(str(script_path))

        markers = generate_markers(script)

        assert len(markers) == 3
        assert markers[0].time == 0.0
        assert markers[1].time == 3.0
        assert markers[2].time == 13.0

    def test_empty_script(self, tmp_path):
        """Test with empty script (no segments)."""
        script = VideoScript(
            name="empty",
            segments=[],
        )

        markers = generate_markers(script)

        assert len(markers) == 0


class TestFormatJsonOutput:
    """Tests for format_json_output function."""

    def test_basic_json_format(self, tmp_path):
        """Test basic JSON output structure."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        markers = generate_markers(script)

        output = format_json_output(script, markers)
        data = json.loads(output)

        assert "script_name" in data
        assert "total_duration" in data
        assert "markers" in data
        assert data["script_name"] == "test-script"
        assert len(data["markers"]) == 4

    def test_marker_fields(self, tmp_path):
        """Test marker fields in JSON output."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "Test"}
        ])
        script = load_script(str(script_path))
        markers = generate_markers(script)

        output = format_json_output(script, markers)
        data = json.loads(output)

        marker = data["markers"][0]
        assert "time" in marker
        assert "event" in marker
        assert "segment_type" in marker
        assert "cue" in marker


class TestFormatMarkdownOutput:
    """Tests for format_markdown_output function."""

    def test_markdown_header(self, tmp_path):
        """Test markdown header format."""
        script_path = create_test_script(tmp_path)
        script = load_script(str(script_path))
        markers = generate_markers(script)

        output = format_markdown_output(script, markers)

        assert "# Narration Guide: test-script" in output
        assert "Total Duration:" in output

    def test_markdown_table(self, tmp_path):
        """Test markdown table format."""
        script_path = create_test_script(tmp_path, [
            {"type": "title", "duration": 3.0, "text": "Test Title"}
        ])
        script = load_script(str(script_path))
        markers = generate_markers(script)

        output = format_markdown_output(script, markers)

        assert "| Time | Event | Cue |" in output
        assert "|------|-------|-----|" in output
        assert "| 0:00 |" in output
        assert '"Test Title"' in output

    def test_markdown_event_format(self, tmp_path):
        """Test event name formatting (title case with spaces)."""
        script_path = create_test_script(tmp_path, [
            {"type": "visualization", "duration": 5.0, "visualizer": "test", "params": {}}
        ])
        script = load_script(str(script_path))
        markers = generate_markers(script)

        output = format_markdown_output(script, markers)

        assert "Visualization Start" in output


class TestMain:
    """Tests for main CLI entry point."""

    def test_basic_json_output(self, tmp_path, monkeypatch, capsys):
        """Test basic JSON output to stdout."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(script_path), '-q'
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "script_name" in data

    def test_markdown_output(self, tmp_path, monkeypatch, capsys):
        """Test markdown output to stdout."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(script_path), '--markdown', '-q'
        ])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "# Narration Guide:" in captured.out

    def test_file_output(self, tmp_path, monkeypatch):
        """Test output to file."""
        script_path = create_test_script(tmp_path)
        output_path = tmp_path / "output.json"
        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(script_path),
            '-o', str(output_path), '-q'
        ])

        result = main()

        assert result == 0
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "markers" in data

    def test_missing_input_file(self, tmp_path, monkeypatch):
        """Test error for missing input file."""
        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(tmp_path / "nonexistent.json")
        ])

        result = main()

        assert result == 1

    def test_invalid_json(self, tmp_path, monkeypatch):
        """Test error for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid }")

        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(bad_file)
        ])

        result = main()

        assert result == 1

    def test_verbose_quiet_mutual_exclusion(self, tmp_path, monkeypatch, capsys):
        """Test that verbose and quiet flags are mutually exclusive."""
        script_path = create_test_script(tmp_path)
        monkeypatch.setattr(sys, 'argv', [
            'narration-export', str(script_path),
            '-v', '-q'  # Both verbose and quiet
        ])

        import pytest
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error


class TestCLIIntegration:
    """Integration tests running CLI as subprocess."""

    def test_cli_help(self):
        """Test CLI --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'narration' in result.stdout.lower()
        assert 'output' in result.stdout.lower()

    def test_cli_json_output(self, tmp_path):
        """Test CLI JSON output."""
        script_path = create_test_script(tmp_path)

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export',
             str(script_path), '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "markers" in data

    def test_cli_markdown_output(self, tmp_path):
        """Test CLI markdown output."""
        script_path = create_test_script(tmp_path)

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export',
             str(script_path), '--markdown', '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "# Narration Guide:" in result.stdout

    def test_cli_file_output(self, tmp_path):
        """Test CLI file output."""
        script_path = create_test_script(tmp_path)
        output_path = tmp_path / "cli_output.json"

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export',
             str(script_path), '-o', str(output_path), '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output_path.exists()

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

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export',
             '-', '-q'],
            input=json.dumps(script),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["script_name"] == "stdin-test"
        assert len(data["markers"]) == 2

    def test_cli_example_script(self):
        """Test CLI with example script from repository."""
        example_path = Path(__file__).parent.parent / 'scripts' / 'videos' / 'lissajous-intro.json'
        if not example_path.exists():
            import pytest
            pytest.skip("Example script not found")

        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.narration_export',
             str(example_path), '-q'],
            capture_output=True,
            text=True,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["script_name"] == "lissajous-intro"
        assert len(data["markers"]) > 0
