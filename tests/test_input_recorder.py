"""Tests for input recorder module."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from atari_style.core.input_recorder import InputRecorder, RecordedKeyframe


class TestRecordedKeyframe(unittest.TestCase):
    """Test RecordedKeyframe dataclass."""

    def test_keyframe_creation(self):
        """Test basic keyframe creation."""
        kf = RecordedKeyframe(time=1.0, x=0.5, y=-0.5, buttons=[0, 2])
        self.assertEqual(kf.time, 1.0)
        self.assertEqual(kf.x, 0.5)
        self.assertEqual(kf.y, -0.5)
        self.assertEqual(kf.buttons, [0, 2])

    def test_keyframe_defaults(self):
        """Test keyframe with default values."""
        kf = RecordedKeyframe(time=0.0)
        self.assertEqual(kf.x, 0.0)
        self.assertEqual(kf.y, 0.0)
        self.assertEqual(kf.buttons, [])

    def test_to_dict(self):
        """Test keyframe serialization."""
        kf = RecordedKeyframe(time=1.5, x=0.333333, y=-0.666666, buttons=[1])
        d = kf.to_dict()

        self.assertEqual(d['time'], 1.5)
        self.assertEqual(d['x'], 0.333)  # Rounded to 3 decimals
        self.assertEqual(d['y'], -0.667)  # Rounded to 3 decimals
        self.assertEqual(d['buttons'], [1])


class TestInputRecorder(unittest.TestCase):
    """Test InputRecorder class."""

    def test_init_defaults(self):
        """Test recorder initialization with defaults."""
        recorder = InputRecorder(duration=10.0)
        self.assertEqual(recorder.duration, 10.0)
        self.assertEqual(recorder.fps, 30)
        self.assertFalse(recorder.digital)
        self.assertFalse(recorder.sparse)

    def test_init_custom(self):
        """Test recorder initialization with custom values."""
        recorder = InputRecorder(
            duration=5.0,
            fps=60,
            digital=True,
            sparse=True,
        )
        self.assertEqual(recorder.duration, 5.0)
        self.assertEqual(recorder.fps, 60)
        self.assertTrue(recorder.digital)
        self.assertTrue(recorder.sparse)

    def test_quantize(self):
        """Test digital quantization."""
        recorder = InputRecorder(duration=1.0, digital=True)

        # Test positive values
        self.assertEqual(recorder._quantize(1.0), 1.0)
        self.assertEqual(recorder._quantize(0.75), 1.0)
        self.assertEqual(recorder._quantize(0.51), 1.0)

        # Test negative values
        self.assertEqual(recorder._quantize(-1.0), -1.0)
        self.assertEqual(recorder._quantize(-0.75), -1.0)
        self.assertEqual(recorder._quantize(-0.51), -1.0)

        # Test neutral zone
        self.assertEqual(recorder._quantize(0.0), 0.0)
        self.assertEqual(recorder._quantize(0.49), 0.0)
        self.assertEqual(recorder._quantize(-0.49), 0.0)

    def test_get_pressed_buttons(self):
        """Test button dictionary to list conversion."""
        recorder = InputRecorder(duration=1.0)

        # No buttons pressed
        self.assertEqual(recorder._get_pressed_buttons({}), [])
        self.assertEqual(recorder._get_pressed_buttons({0: False, 1: False}), [])

        # Some buttons pressed
        self.assertEqual(
            recorder._get_pressed_buttons({0: True, 1: False, 2: True}),
            [0, 2]
        )

        # All buttons pressed
        self.assertEqual(
            recorder._get_pressed_buttons({0: True, 1: True, 2: True}),
            [0, 1, 2]
        )

    def test_state_changed_first_call(self):
        """Test state change detection on first call."""
        recorder = InputRecorder(duration=1.0)

        # First call should always return True
        self.assertTrue(recorder._state_changed(0.0, 0.0, []))

    def test_state_changed_axis(self):
        """Test state change detection for axis movement."""
        recorder = InputRecorder(duration=1.0)

        # Record initial state
        recorder._record_keyframe(0.0, 0.0, 0.0, [])

        # Small change (below threshold)
        self.assertFalse(recorder._state_changed(0.01, 0.01, []))

        # Large change
        self.assertTrue(recorder._state_changed(0.5, 0.0, []))
        self.assertTrue(recorder._state_changed(0.0, 0.5, []))

    def test_state_changed_buttons(self):
        """Test state change detection for buttons."""
        recorder = InputRecorder(duration=1.0)

        # Record initial state
        recorder._record_keyframe(0.0, 0.0, 0.0, [])

        # Button press
        self.assertTrue(recorder._state_changed(0.0, 0.0, [0]))

        # Record button press
        recorder._record_keyframe(0.1, 0.0, 0.0, [0])

        # Same button state
        self.assertFalse(recorder._state_changed(0.0, 0.0, [0]))

        # Button release
        self.assertTrue(recorder._state_changed(0.0, 0.0, []))

    def test_to_dict(self):
        """Test recording to dictionary conversion."""
        recorder = InputRecorder(duration=2.0, fps=30)
        recorder.keyframes = [
            RecordedKeyframe(time=0.0, x=0.0, y=0.0, buttons=[]),
            RecordedKeyframe(time=1.0, x=1.0, y=0.0, buttons=[0]),
        ]

        d = recorder.to_dict()

        self.assertEqual(d['duration'], 2.0)
        self.assertEqual(d['fps'], 30)
        self.assertEqual(d['interpolation'], 'smooth')
        self.assertEqual(len(d['keyframes']), 2)
        self.assertEqual(d['keyframes'][0]['time'], 0.0)
        self.assertEqual(d['keyframes'][1]['x'], 1.0)

    def test_to_dict_digital_mode(self):
        """Test that digital mode sets step interpolation."""
        recorder = InputRecorder(duration=1.0, digital=True)
        recorder.keyframes = []

        d = recorder.to_dict()
        self.assertEqual(d['interpolation'], 'step')

    def test_save(self):
        """Test saving recording to file."""
        recorder = InputRecorder(duration=1.0, fps=30)
        recorder.keyframes = [
            RecordedKeyframe(time=0.0, x=0.0, y=0.0, buttons=[]),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            recorder.save(temp_path)

            # Verify file contents
            with open(temp_path, 'r') as f:
                data = json.load(f)

            self.assertEqual(data['fps'], 30)
            self.assertEqual(len(data['keyframes']), 1)

        finally:
            os.unlink(temp_path)


class TestInputRecorderIntegration(unittest.TestCase):
    """Integration tests with mocked input handler."""

    @patch('atari_style.core.input_recorder.InputHandler')
    @patch('atari_style.core.input_recorder.time.sleep')
    def test_record_basic(self, mock_sleep, mock_handler_class):
        """Test basic recording with mocked joystick."""
        # Setup mock handler
        mock_handler = MagicMock()
        mock_handler.verify_joystick.return_value = {
            'connected': True,
            'name': 'Mock Joystick',
            'axes': 2,
            'buttons': 6,
        }
        mock_handler.get_joystick_state.return_value = (0.0, 0.0)
        mock_handler.get_joystick_buttons.return_value = {i: False for i in range(6)}
        mock_handler_class.return_value = mock_handler

        # Record 0.1 seconds at 10 fps = 1 frame
        recorder = InputRecorder(duration=0.1, fps=10)
        keyframes = recorder.record()

        # Verify recording
        self.assertEqual(len(keyframes), 1)
        self.assertEqual(keyframes[0].x, 0.0)
        self.assertEqual(keyframes[0].y, 0.0)

        # Verify cleanup was called
        mock_handler.cleanup.assert_called_once()

    @patch('atari_style.core.input_recorder.InputHandler')
    @patch('atari_style.core.input_recorder.time.sleep')
    def test_record_sparse_mode(self, mock_sleep, mock_handler_class):
        """Test sparse mode only records on state change."""
        # Setup mock handler
        mock_handler = MagicMock()
        mock_handler.verify_joystick.return_value = {
            'connected': True,
            'name': 'Mock Joystick',
            'axes': 2,
            'buttons': 6,
        }
        # First frame: neutral, second frame: still neutral, third frame: movement
        mock_handler.get_joystick_state.side_effect = [
            (0.0, 0.0),  # Frame 0 - recorded (first frame)
            (0.0, 0.0),  # Frame 1 - not recorded (no change)
            (0.8, 0.0),  # Frame 2 - recorded (state changed)
        ]
        mock_handler.get_joystick_buttons.return_value = {i: False for i in range(6)}
        mock_handler_class.return_value = mock_handler

        # Record 0.3 seconds at 10 fps = 3 frames
        recorder = InputRecorder(duration=0.3, fps=10, sparse=True)
        keyframes = recorder.record()

        # Sparse mode should record fewer keyframes than frames
        # First frame always recorded, plus any state changes
        self.assertLess(len(keyframes), 3)
        self.assertGreaterEqual(len(keyframes), 1)

    @patch('atari_style.core.input_recorder.InputHandler')
    @patch('atari_style.core.input_recorder.time.sleep')
    def test_record_digital_mode(self, mock_sleep, mock_handler_class):
        """Test digital mode quantizes values to -1/0/1."""
        # Setup mock handler
        mock_handler = MagicMock()
        mock_handler.verify_joystick.return_value = {
            'connected': True,
            'name': 'Mock Joystick',
            'axes': 2,
            'buttons': 6,
        }
        # Return analog values that should be quantized
        mock_handler.get_joystick_state.return_value = (0.75, -0.9)
        mock_handler.get_joystick_buttons.return_value = {i: False for i in range(6)}
        mock_handler_class.return_value = mock_handler

        # Record 0.1 seconds at 10 fps = 1 frame
        recorder = InputRecorder(duration=0.1, fps=10, digital=True)
        keyframes = recorder.record()

        # Values should be quantized
        self.assertEqual(len(keyframes), 1)
        self.assertEqual(keyframes[0].x, 1.0)   # 0.75 > 0.5 -> 1.0
        self.assertEqual(keyframes[0].y, -1.0)  # -0.9 < -0.5 -> -1.0

    @patch('atari_style.core.input_recorder.InputHandler')
    @patch('atari_style.core.input_recorder.time.sleep')
    def test_record_no_joystick(self, mock_sleep, mock_handler_class):
        """Test recording with no joystick connected."""
        # Setup mock handler with no joystick
        mock_handler = MagicMock()
        mock_handler.verify_joystick.return_value = {
            'connected': False,
            'name': None,
            'axes': 0,
            'buttons': 0,
        }
        # Return neutral values (no joystick)
        mock_handler.get_joystick_state.return_value = (0.0, 0.0)
        mock_handler.get_joystick_buttons.return_value = {}
        mock_handler_class.return_value = mock_handler

        # Record 0.1 seconds at 10 fps = 1 frame
        recorder = InputRecorder(duration=0.1, fps=10)
        keyframes = recorder.record()

        # Should still record (with neutral values)
        self.assertEqual(len(keyframes), 1)
        self.assertEqual(keyframes[0].x, 0.0)
        self.assertEqual(keyframes[0].y, 0.0)
        self.assertEqual(keyframes[0].buttons, [])


if __name__ == '__main__':
    unittest.main()
