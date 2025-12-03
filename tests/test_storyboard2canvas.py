"""Tests for storyboard2canvas connector."""

import json
import tempfile
import unittest
from pathlib import Path

from atari_style.connectors.storyboard2canvas import (
    StoryboardConverter,
    CanvasBox,
    storyboard_to_canvas
)


class TestStoryboardConverter(unittest.TestCase):
    """Test StoryboardConverter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = StoryboardConverter()
        self.sample_storyboard = {
            'version': '1.0',
            'title': 'Test Storyboard',
            'description': 'A test storyboard for unit testing',
            'composite': 'plasma_lissajous',
            'format': 'youtube_shorts',
            'fps': 30,
            'keyframes': [
                {
                    'id': 'intro',
                    'time': 0.0,
                    'params': [0.1, 0.2, 0.15, 0.1],
                    'note': 'Opening scene'
                },
                {
                    'id': 'peak',
                    'time': 30.0,
                    'params': [0.8, 0.9, 0.85, 0.9],
                    'note': 'Maximum intensity'
                },
                {
                    'id': 'outro',
                    'time': 45.0,
                    'params': [0.4, 0.5, 0.45, 0.5],
                    'note': 'Closing'
                }
            ]
        }

    def test_init_default_dimensions(self):
        """Test default canvas dimensions."""
        converter = StoryboardConverter()
        self.assertEqual(converter.world_width, 2000)
        self.assertEqual(converter.world_height, 800)

    def test_init_custom_dimensions(self):
        """Test custom canvas dimensions via constructor."""
        converter = StoryboardConverter(world_width=1920, world_height=1080)
        self.assertEqual(converter.world_width, 1920)
        self.assertEqual(converter.world_height, 1080)

    def test_calculate_intensity_low(self):
        """Test intensity calculation for low values."""
        self.assertEqual(self.converter.calculate_intensity([0.1, 0.2]), 'low')
        self.assertEqual(self.converter.calculate_intensity([0.0, 0.0, 0.0]), 'low')
        self.assertEqual(self.converter.calculate_intensity([0.29]), 'low')

    def test_calculate_intensity_medium(self):
        """Test intensity calculation for medium values."""
        self.assertEqual(self.converter.calculate_intensity([0.3, 0.4]), 'medium')
        self.assertEqual(self.converter.calculate_intensity([0.4, 0.5, 0.4]), 'medium')
        self.assertEqual(self.converter.calculate_intensity([0.49]), 'medium')

    def test_calculate_intensity_high(self):
        """Test intensity calculation for high values."""
        self.assertEqual(self.converter.calculate_intensity([0.5, 0.6]), 'high')
        self.assertEqual(self.converter.calculate_intensity([0.6, 0.7, 0.65]), 'high')
        self.assertEqual(self.converter.calculate_intensity([0.69]), 'high')

    def test_calculate_intensity_peak(self):
        """Test intensity calculation for peak values."""
        self.assertEqual(self.converter.calculate_intensity([0.7, 0.8]), 'peak')
        self.assertEqual(self.converter.calculate_intensity([0.9, 1.0, 0.95]), 'peak')
        self.assertEqual(self.converter.calculate_intensity([1.0]), 'peak')

    def test_calculate_intensity_empty_params(self):
        """Test intensity calculation with empty params."""
        self.assertEqual(self.converter.calculate_intensity([]), 'low')

    def test_format_params(self):
        """Test parameter formatting."""
        result = self.converter.format_params([0.1, 0.25, 0.333])
        self.assertEqual(result, '[0.10, 0.25, 0.33]')

    def test_format_params_empty(self):
        """Test formatting empty params."""
        result = self.converter.format_params([])
        self.assertEqual(result, '[]')

    def test_create_header_box(self):
        """Test header box creation."""
        box = self.converter.create_header_box(self.sample_storyboard)

        self.assertEqual(box.id, 1)
        self.assertEqual(box.title, 'Test Storyboard')
        self.assertEqual(box.color, 6)  # Cyan for header
        self.assertIn('Composite: plasma_lissajous', box.content)
        self.assertIn('Keyframes: 3', box.content)

    def test_create_keyframe_box(self):
        """Test keyframe box creation."""
        keyframe = self.sample_storyboard['keyframes'][0]
        box = self.converter.create_keyframe_box(keyframe, 0, 2)

        self.assertEqual(box.id, 2)
        self.assertEqual(box.title, 'intro')
        self.assertEqual(box.color, 4)  # Blue for low intensity
        self.assertIn('Time: 0.0s', box.content)

    def test_create_keyframe_box_peak_intensity(self):
        """Test keyframe box with peak intensity gets red color."""
        keyframe = self.sample_storyboard['keyframes'][1]  # peak
        box = self.converter.create_keyframe_box(keyframe, 1, 3)

        self.assertEqual(box.color, 1)  # Red for peak intensity

    def test_create_keyframe_box_medium_intensity(self):
        """Test keyframe box with medium intensity gets green color."""
        keyframe = self.sample_storyboard['keyframes'][2]  # outro
        box = self.converter.create_keyframe_box(keyframe, 2, 4)

        self.assertEqual(box.color, 2)  # Green for medium intensity

    def test_create_keyframe_box_position(self):
        """Test keyframe box horizontal positioning."""
        boxes = []
        for idx, kf in enumerate(self.sample_storyboard['keyframes']):
            box = self.converter.create_keyframe_box(kf, idx, idx + 2)
            boxes.append(box)

        # Check horizontal spacing
        self.assertEqual(boxes[0].x, 80)  # START_X
        self.assertEqual(boxes[1].x, 80 + 280)  # START_X + SPACING
        self.assertEqual(boxes[2].x, 80 + 560)  # START_X + 2*SPACING

    def test_convert_creates_correct_box_count(self):
        """Test convert creates header + keyframe boxes."""
        boxes = self.converter.convert(self.sample_storyboard)

        # 1 header + 3 keyframes = 4 boxes
        self.assertEqual(len(boxes), 4)

    def test_to_canvas_format_header(self):
        """Test canvas format has correct header."""
        self.converter.convert(self.sample_storyboard)
        canvas = self.converter.to_canvas_format()

        lines = canvas.split('\n')
        self.assertEqual(lines[0], 'BOXES_CANVAS_V1')
        self.assertEqual(lines[1], '2000 800')
        self.assertEqual(lines[2], '4')  # box count

    def test_to_canvas_format_custom_dimensions(self):
        """Test canvas format respects custom dimensions."""
        converter = StoryboardConverter(world_width=1920, world_height=1080)
        converter.convert(self.sample_storyboard)
        canvas = converter.to_canvas_format()

        lines = canvas.split('\n')
        self.assertEqual(lines[1], '1920 1080')

    def test_note_truncation(self):
        """Test long notes are truncated."""
        long_note = 'A' * 100  # Very long note
        keyframe = {
            'id': 'test',
            'time': 0.0,
            'params': [0.5],
            'note': long_note
        }
        box = self.converter.create_keyframe_box(keyframe, 0, 1)

        # Note should be truncated to 45 chars with ...
        for line in box.content:
            self.assertLessEqual(len(line), 45)

    def test_title_truncation(self):
        """Test long titles are truncated."""
        self.sample_storyboard['title'] = 'A' * 100
        box = self.converter.create_header_box(self.sample_storyboard)

        self.assertLessEqual(len(box.title), 40)


class TestStoryboardToCanvasFunction(unittest.TestCase):
    """Test storyboard_to_canvas convenience function."""

    def setUp(self):
        """Create temporary storyboard file."""
        self.sample_storyboard = {
            'title': 'Test',
            'composite': 'test',
            'keyframes': [
                {'id': 'kf1', 'time': 0.0, 'params': [0.5], 'note': 'test'}
            ]
        }

    def test_storyboard_to_canvas_returns_string(self):
        """Test function returns canvas string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_storyboard, f)
            f.flush()

            result = storyboard_to_canvas(f.name)

            self.assertIsInstance(result, str)
            self.assertTrue(result.startswith('BOXES_CANVAS_V1'))

    def test_storyboard_to_canvas_writes_file(self):
        """Test function writes to output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_storyboard, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as out:
            output_path = out.name

        storyboard_to_canvas(input_path, output_path)

        with open(output_path) as f:
            content = f.read()

        self.assertTrue(content.startswith('BOXES_CANVAS_V1'))


class TestLoadStoryboard(unittest.TestCase):
    """Test storyboard loading."""

    def test_load_valid_json(self):
        """Test loading valid JSON file."""
        converter = StoryboardConverter()
        sample = {'title': 'Test', 'keyframes': []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample, f)
            f.flush()

            result = converter.load_storyboard(f.name)

        self.assertEqual(result['title'], 'Test')

    def test_load_missing_file_raises(self):
        """Test loading missing file raises FileNotFoundError."""
        converter = StoryboardConverter()

        with self.assertRaises(FileNotFoundError):
            converter.load_storyboard('/nonexistent/file.json')

    def test_load_invalid_json_raises(self):
        """Test loading invalid JSON raises JSONDecodeError."""
        converter = StoryboardConverter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json {{{')
            f.flush()

            with self.assertRaises(json.JSONDecodeError):
                converter.load_storyboard(f.name)


if __name__ == '__main__':
    unittest.main()
