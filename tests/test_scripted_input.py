"""Tests for scripted input handler."""

import json
import tempfile
import unittest

from atari_style.core.scripted_input import (
    ScriptedInputHandler,
    InputScript,
    InputKeyframe,
    create_simple_script,
)


class TestInputScript(unittest.TestCase):
    """Test InputScript parsing and creation."""

    def test_from_dict_basic(self):
        """Test creating script from dictionary."""
        data = {
            'duration': 10.0,
            'fps': 30,
            'keyframes': [
                {'time': 0.0, 'x': 0.0, 'y': 0.0, 'buttons': []},
                {'time': 5.0, 'x': 1.0, 'y': -1.0, 'buttons': [0, 1]},
            ]
        }
        script = InputScript.from_dict(data)

        self.assertEqual(script.duration, 10.0)
        self.assertEqual(script.fps, 30)
        self.assertEqual(len(script.keyframes), 2)

    def test_from_dict_defaults(self):
        """Test default values when fields are missing."""
        data = {'keyframes': []}
        script = InputScript.from_dict(data)

        self.assertEqual(script.duration, 10.0)
        self.assertEqual(script.fps, 30)
        self.assertEqual(script.interpolation, 'smooth')

    def test_from_file(self):
        """Test loading script from JSON file."""
        data = {
            'name': 'Test Script',
            'duration': 5.0,
            'fps': 60,
            'keyframes': [
                {'time': 0.0, 'x': 0.5, 'y': 0.5, 'buttons': [0]}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()

            script = InputScript.from_file(f.name)

        self.assertEqual(script.name, 'Test Script')
        self.assertEqual(script.duration, 5.0)
        self.assertEqual(script.fps, 60)

    def test_keyframes_sorted_by_time(self):
        """Test that keyframes are sorted by time."""
        data = {
            'keyframes': [
                {'time': 5.0, 'x': 1.0, 'y': 0.0},
                {'time': 0.0, 'x': 0.0, 'y': 0.0},
                {'time': 2.5, 'x': 0.5, 'y': 0.0},
            ]
        }
        script = InputScript.from_dict(data)

        times = [kf.time for kf in script.keyframes]
        self.assertEqual(times, [0.0, 2.5, 5.0])


class TestScriptedInputHandler(unittest.TestCase):
    """Test ScriptedInputHandler functionality."""

    def setUp(self):
        """Create a test script."""
        self.script = create_simple_script(
            duration=10.0,
            movements=[
                (0.0, 0.0, 0.0, []),
                (5.0, 1.0, -1.0, [0]),
                (10.0, 0.0, 0.0, []),
            ],
            fps=30,
            interpolation='linear'
        )
        self.handler = ScriptedInputHandler(script=self.script)

    def test_init_with_script(self):
        """Test initialization with script object."""
        self.assertEqual(self.handler.script.duration, 10.0)
        self.assertTrue(self.handler.joystick_initialized)

    def test_get_frame_count(self):
        """Test frame count calculation."""
        self.assertEqual(self.handler.get_frame_count(), 300)  # 10s * 30fps

    def test_is_active_before_start(self):
        """Test is_active returns False before start."""
        self.assertFalse(self.handler.is_active())

    def test_is_active_after_start(self):
        """Test is_active returns True after start."""
        self.handler.start()
        self.assertTrue(self.handler.is_active())

    def test_is_active_past_duration(self):
        """Test is_active returns False past duration."""
        self.handler.start()
        self.handler.current_time = 15.0
        self.assertFalse(self.handler.is_active())

    def test_get_joystick_state_at_start(self):
        """Test joystick state at time 0."""
        self.handler.current_time = 0.0
        x, y = self.handler.get_joystick_state()
        self.assertEqual(x, 0.0)
        self.assertEqual(y, 0.0)

    def test_get_joystick_state_interpolated(self):
        """Test linear interpolation of joystick position."""
        self.handler.current_time = 2.5  # Halfway between 0 and 5
        x, y = self.handler.get_joystick_state()
        self.assertAlmostEqual(x, 0.5, places=1)
        self.assertAlmostEqual(y, -0.5, places=1)

    def test_get_joystick_buttons_at_keyframe(self):
        """Test button state at keyframe time."""
        self.handler.current_time = 5.0
        buttons = self.handler.get_joystick_buttons()
        self.assertTrue(buttons[0])
        self.assertFalse(buttons[1])

    def test_get_joystick_buttons_between_keyframes(self):
        """Test button state uses previous keyframe."""
        self.handler.current_time = 7.0  # Between 5.0 (buttons=[0]) and 10.0 (buttons=[])
        buttons = self.handler.get_joystick_buttons()
        self.assertTrue(buttons[0])

    def test_verify_joystick(self):
        """Test mock joystick verification."""
        info = self.handler.verify_joystick()
        self.assertTrue(info['connected'])
        self.assertEqual(info['axes'], 2)
        self.assertEqual(info['buttons'], 12)

    def test_advance_frame(self):
        """Test frame advancement."""
        self.handler.current_time = 0.0
        self.handler.advance_frame(1/30)
        self.assertAlmostEqual(self.handler.current_time, 1/30)

    def test_reset(self):
        """Test reset functionality."""
        self.handler.start()
        self.handler.current_time = 5.0
        self.handler.reset()
        self.assertEqual(self.handler.current_time, 0.0)
        self.assertFalse(self.handler.started)


class TestStepInterpolation(unittest.TestCase):
    """Test step interpolation mode."""

    def test_step_uses_previous_keyframe(self):
        """Test that step interpolation uses previous keyframe."""
        script = create_simple_script(
            duration=10.0,
            movements=[
                (0.0, 0.0, 0.0, []),
                (5.0, 1.0, 1.0, []),
            ],
            interpolation='step'
        )
        handler = ScriptedInputHandler(script=script)

        # At time 2.5 (between keyframes), should use previous keyframe
        handler.current_time = 2.5
        x, y = handler.get_joystick_state()
        self.assertEqual(x, 0.0)
        self.assertEqual(y, 0.0)

        # At time 5.0, should jump to new position
        handler.current_time = 5.0
        x, y = handler.get_joystick_state()
        self.assertEqual(x, 1.0)
        self.assertEqual(y, 1.0)


class TestCreateSimpleScript(unittest.TestCase):
    """Test helper function for creating scripts."""

    def test_create_simple_script(self):
        """Test creating script programmatically."""
        script = create_simple_script(
            duration=5.0,
            movements=[
                (0.0, 0.0, 0.0, []),
                (2.5, 0.5, -0.5, [0, 1]),
                (5.0, 1.0, 1.0, [2]),
            ],
            fps=60,
            interpolation='smooth'
        )

        self.assertEqual(script.duration, 5.0)
        self.assertEqual(script.fps, 60)
        self.assertEqual(script.interpolation, 'smooth')
        self.assertEqual(len(script.keyframes), 3)


if __name__ == '__main__':
    unittest.main()
