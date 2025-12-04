"""Tests for video scripting framework."""

import json
import tempfile
from pathlib import Path

from atari_style.core.video_script import (
    VideoScript, Segment, TitleSegment, VisualizationSegment,
    SweepSegment, TransitionSegment, PauseSegment,
    SegmentType, EasingType, TransitionConfig, FORMAT_PRESETS
)


class TestSegmentTypes:
    """Tests for segment type parsing."""

    def test_title_segment(self):
        data = {
            "type": "title",
            "duration": 3.0,
            "text": "Hello World",
            "subtitle": "Subtitle text"
        }
        segment = Segment.from_dict(data)
        assert isinstance(segment, TitleSegment)
        assert segment.get_type() == SegmentType.TITLE
        assert segment.duration == 3.0
        assert segment.text == "Hello World"
        assert segment.subtitle == "Subtitle text"

    def test_visualization_segment(self):
        data = {
            "type": "visualization",
            "duration": 10.0,
            "visualizer": "lissajous",
            "params": {"a": 1, "b": 2, "delta": 0.5},
            "color_mode": 1
        }
        segment = Segment.from_dict(data)
        assert isinstance(segment, VisualizationSegment)
        assert segment.get_type() == SegmentType.VISUALIZATION
        assert segment.visualizer == "lissajous"
        assert segment.params["a"] == 1
        assert segment.color_mode == 1

    def test_sweep_segment(self):
        data = {
            "type": "sweep",
            "duration": 15.0,
            "visualizer": "lissajous",
            "from": {"a": 1, "b": 1},
            "to": {"a": 3, "b": 4},
            "easing": "linear"
        }
        segment = Segment.from_dict(data)
        assert isinstance(segment, SweepSegment)
        assert segment.get_type() == SegmentType.SWEEP
        assert segment.from_params["a"] == 1
        assert segment.to_params["a"] == 3
        assert segment.easing == EasingType.LINEAR

    def test_transition_segment(self):
        data = {"type": "transition", "duration": 1.0, "effect": "fade"}
        segment = Segment.from_dict(data)
        assert isinstance(segment, TransitionSegment)
        assert segment.effect == "fade"

    def test_pause_segment(self):
        data = {"type": "pause", "duration": 2.0}
        segment = Segment.from_dict(data)
        assert isinstance(segment, PauseSegment)
        assert segment.duration == 2.0


class TestVideoScript:
    """Tests for VideoScript class."""

    def test_creation(self):
        script = VideoScript(
            name="test-script",
            segments=[
                TitleSegment(duration=3.0, text="Title"),
                VisualizationSegment(duration=10.0, visualizer="lissajous")
            ]
        )
        assert script.name == "test-script"
        assert script.segment_count == 2
        assert script.total_duration == 13.0

    def test_from_dict(self):
        data = {
            "name": "test",
            "version": "2.0",
            "format": "youtube_shorts",
            "segments": [
                {"type": "title", "duration": 3.0, "text": "Hello"},
                {"type": "visualization", "duration": 10.0, "visualizer": "test"}
            ]
        }
        script = VideoScript.from_dict(data)
        assert script.name == "test"
        assert script.version == "2.0"
        assert script.format.name == "youtube_shorts"
        assert script.format.is_vertical
        assert len(script.segments) == 2

    def test_validation_valid_script(self):
        script = VideoScript(
            name="valid",
            segments=[
                TitleSegment(duration=3.0, text="Title"),
                VisualizationSegment(duration=10.0, visualizer="lissajous")
            ]
        )
        errors = script.validate()
        assert len(errors) == 0

    def test_validation_missing_name(self):
        script = VideoScript(
            name="",
            segments=[TitleSegment(duration=3.0, text="Title")]
        )
        errors = script.validate()
        assert any("name is required" in e for e in errors)

    def test_validation_no_segments(self):
        script = VideoScript(name="test", segments=[])
        errors = script.validate()
        assert any("at least one segment" in e for e in errors)

    def test_validation_duration_limit(self):
        # YouTube Shorts has 60s limit
        script = VideoScript(
            name="test",
            segments=[VisualizationSegment(duration=120.0, visualizer="test")],
            format=FORMAT_PRESETS['youtube_shorts']
        )
        errors = script.validate()
        assert any("exceeds format limit" in e for e in errors)

    def test_validation_missing_visualizer(self):
        script = VideoScript(
            name="test",
            segments=[VisualizationSegment(duration=10.0, visualizer="")]
        )
        errors = script.validate()
        assert any("visualizer is required" in e for e in errors)

    def test_to_json_roundtrip(self):
        original = VideoScript(
            name="roundtrip-test",
            version="1.5",
            description="Test description",
            segments=[
                TitleSegment(duration=3.0, text="Title", subtitle="Sub"),
                SweepSegment(
                    duration=10.0,
                    visualizer="lissajous",
                    from_params={"a": 1},
                    to_params={"a": 2}
                )
            ]
        )
        json_str = original.to_json()
        data = json.loads(json_str)
        restored = VideoScript.from_dict(data)

        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.segment_count == original.segment_count
        assert restored.total_duration == original.total_duration


class TestFileOperations:
    """Tests for file I/O operations."""

    def test_save_and_load(self):
        script = VideoScript(
            name="file-test",
            segments=[TitleSegment(duration=3.0, text="Test")]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test-script.json"
            script.save(path)

            assert path.exists()

            loaded = VideoScript.from_file(path)
            assert loaded.name == script.name
            assert loaded.segment_count == script.segment_count

    def test_load_example_script(self):
        # Test loading the example lissajous script
        example_path = Path(__file__).parent.parent / "scripts" / "videos" / "lissajous-intro.json"
        if example_path.exists():
            script = VideoScript.from_file(example_path)
            assert script.name == "lissajous-intro"
            assert script.segment_count > 0
            errors = script.validate()
            assert len(errors) == 0


class TestFormatPresets:
    """Tests for format presets."""

    def test_preset_existence(self):
        expected = ['preview', 'youtube_landscape', 'youtube_shorts', '4k', 'instagram_square', 'twitter']
        for name in expected:
            assert name in FORMAT_PRESETS

    def test_youtube_shorts_vertical(self):
        shorts = FORMAT_PRESETS['youtube_shorts']
        assert shorts.is_vertical
        assert shorts.max_duration == 60

    def test_instagram_square(self):
        insta = FORMAT_PRESETS['instagram_square']
        assert insta.is_square
        assert insta.width == insta.height


class TestTransitionConfig:
    """Tests for TransitionConfig."""

    def test_from_dict(self):
        data = {"easing": "ease_in_out", "duration": 2.5}
        config = TransitionConfig.from_dict(data)
        assert config.easing == EasingType.EASE_IN_OUT
        assert config.duration == 2.5

    def test_defaults(self):
        config = TransitionConfig.from_dict({})
        assert config.easing == EasingType.SMOOTH
        assert config.duration == 1.0
