"""Tests for aspect calibration CLI and config module."""

import json
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from atari_style.core.config import (
    Config,
    DEFAULT_CHAR_ASPECT,
)
from atari_style.tools.aspect_calibration import (
    draw_circle,
    draw_crosshairs,
    draw_instructions,
    run_interactive_calibration,
    show_current_value,
    reset_to_default,
    main,
    ASPECT_INCREMENT,
    MIN_ASPECT_RATIO,
    MAX_ASPECT_RATIO,
)


class TestConfig:
    """Tests for Config class."""

    def test_load_missing_file_returns_defaults(self, tmp_path, monkeypatch):
        """Test Config.load() returns defaults when file doesn't exist."""
        # Point config to non-existent file
        fake_config = tmp_path / 'nonexistent' / 'config.json'
        monkeypatch.setattr(
            'atari_style.core.config.CONFIG_FILE',
            fake_config
        )

        config = Config.load()

        assert config.char_aspect == DEFAULT_CHAR_ASPECT

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """Test Config.save() and load() round-trip."""
        # Point config to temp directory
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)

        # Save custom value
        config = Config(char_aspect=0.75)
        config.save()

        # Verify file was created
        assert fake_file.exists()

        # Load and verify
        loaded = Config.load()
        assert loaded.char_aspect == 0.75

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        """Test Config.save() creates directory if needed."""
        fake_dir = tmp_path / 'nested' / 'path' / '.atari-style'
        fake_file = fake_dir / 'config.json'
        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)

        assert not fake_dir.exists()

        config = Config()
        config.save()

        assert fake_dir.exists()
        assert fake_file.exists()

    def test_load_invalid_json_returns_defaults(self, tmp_path, monkeypatch):
        """Test Config.load() returns defaults for invalid JSON."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{ invalid json }')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)

        config = Config.load()

        assert config.char_aspect == DEFAULT_CHAR_ASPECT

    def test_load_with_extra_fields_ignores_unknown(self, tmp_path, monkeypatch):
        """Test Config.load() ignores unknown fields in JSON."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.6, "unknown_field": "value"}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)

        config = Config.load()

        assert config.char_aspect == 0.6

    def test_default_char_aspect_value(self):
        """Test default char_aspect is 0.5."""
        assert DEFAULT_CHAR_ASPECT == 0.5

        config = Config()
        assert config.char_aspect == 0.5

    def test_load_invalid_data_type_returns_defaults(self, tmp_path, monkeypatch):
        """Test Config.load() returns defaults for invalid data types (TypeError)."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        # Write a string value where float is expected - causes TypeError
        fake_file.write_text('{"char_aspect": "not_a_number"}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)

        config = Config.load()

        # Should return defaults when TypeError occurs
        assert config.char_aspect == DEFAULT_CHAR_ASPECT


class TestShowCurrentValue:
    """Tests for show_current_value function."""

    def test_show_plain_output(self, tmp_path, monkeypatch, capsys):
        """Test --show outputs current value."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.55}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )

        result = show_current_value(json_output=False, quiet=False)

        assert result == 0
        captured = capsys.readouterr()
        assert '0.55' in captured.out

    def test_show_json_output(self, tmp_path, monkeypatch, capsys):
        """Test --show --json outputs JSON format."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.55}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )

        result = show_current_value(json_output=True, quiet=False)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['char_aspect'] == 0.55
        assert data['default'] == DEFAULT_CHAR_ASPECT


class TestResetToDefault:
    """Tests for reset_to_default function."""

    def test_reset_saves_default(self, tmp_path, monkeypatch, capsys):
        """Test --reset saves default value."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        # Start with non-default value
        fake_file.write_text('{"char_aspect": 0.75}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )

        result = reset_to_default(json_output=False, quiet=False)

        assert result == 0

        # Verify file was updated
        loaded = Config.load()
        assert loaded.char_aspect == DEFAULT_CHAR_ASPECT

    def test_reset_json_output(self, tmp_path, monkeypatch, capsys):
        """Test --reset --json outputs JSON format."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.75}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )

        result = reset_to_default(json_output=True, quiet=False)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['char_aspect'] == DEFAULT_CHAR_ASPECT
        assert data['reset'] is True


class TestMain:
    """Tests for main CLI entry point."""

    def test_show_flag(self, tmp_path, monkeypatch, capsys):
        """Test --show flag through main."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.6}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )
        monkeypatch.setattr(sys, 'argv', ['aspect-calibration', '--show'])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert '0.6' in captured.out

    def test_reset_flag(self, tmp_path, monkeypatch, capsys):
        """Test --reset flag through main."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.75}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )
        monkeypatch.setattr(sys, 'argv', ['aspect-calibration', '--reset'])

        result = main()

        assert result == 0
        loaded = Config.load()
        assert loaded.char_aspect == DEFAULT_CHAR_ASPECT

    def test_json_flag_with_show(self, tmp_path, monkeypatch, capsys):
        """Test --json flag with --show."""
        fake_dir = tmp_path / '.atari-style'
        fake_file = fake_dir / 'config.json'
        fake_dir.mkdir(parents=True)
        fake_file.write_text('{"char_aspect": 0.65}')

        monkeypatch.setattr('atari_style.core.config.CONFIG_DIR', fake_dir)
        monkeypatch.setattr('atari_style.core.config.CONFIG_FILE', fake_file)
        monkeypatch.setattr(
            'atari_style.tools.aspect_calibration.Config',
            Config
        )
        monkeypatch.setattr(
            sys, 'argv', ['aspect-calibration', '--show', '--json']
        )

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'char_aspect' in data

    def test_verbose_quiet_mutual_exclusion(self, monkeypatch, capsys):
        """Test -v and -q flags are mutually exclusive."""
        monkeypatch.setattr(
            sys, 'argv', ['aspect-calibration', '--show', '-v', '-q']
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2

    @patch('atari_style.tools.aspect_calibration.run_interactive_calibration')
    def test_keyboard_interrupt_returns_130(self, mock_run, monkeypatch, capsys):
        """Test KeyboardInterrupt returns exit code 130."""
        mock_run.side_effect = KeyboardInterrupt()
        monkeypatch.setattr(sys, 'argv', ['aspect-calibration'])

        result = main()

        assert result == 130
        captured = capsys.readouterr()
        assert 'Interrupted' in captured.err


class TestCLIIntegration:
    """Integration tests running CLI as subprocess."""

    def test_cli_help(self):
        """Test --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.aspect_calibration',
             '--help'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert 'aspect' in result.stdout.lower()
        assert '--show' in result.stdout
        assert '--reset' in result.stdout

    def test_cli_show_flag(self):
        """Test CLI --show flag as subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.aspect_calibration',
             '--show'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should show some aspect ratio value
        assert 'aspect ratio' in result.stdout.lower() or \
               'char_aspect' in result.stdout.lower() or \
               '0.' in result.stdout

    def test_cli_json_output(self):
        """Test CLI --json output."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.tools.aspect_calibration',
             '--show', '--json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'char_aspect' in data
        assert 'default' in data
        # Aspect ratio should be between MIN and MAX
        assert MIN_ASPECT_RATIO <= data['char_aspect'] <= MAX_ASPECT_RATIO


class TestDrawingFunctions:
    """Tests for drawing helper functions."""

    def test_draw_circle_calls_set_pixel(self):
        """Test draw_circle calls renderer.set_pixel."""
        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24

        draw_circle(mock_renderer, 40, 12, 5, 0.5)

        assert mock_renderer.set_pixel.called
        # Should call set_pixel many times for circle points
        assert mock_renderer.set_pixel.call_count >= 360

    def test_draw_crosshairs_calls_set_pixel(self):
        """Test draw_crosshairs calls renderer.set_pixel."""
        mock_renderer = MagicMock()

        draw_crosshairs(mock_renderer, 40, 12, 10)

        assert mock_renderer.set_pixel.called
        # Crosshairs: horizontal + vertical + center
        assert mock_renderer.set_pixel.call_count >= 20

    def test_draw_instructions_calls_draw_text(self):
        """Test draw_instructions calls renderer.draw_text."""
        mock_renderer = MagicMock()

        draw_instructions(mock_renderer, 0.5, 10)

        assert mock_renderer.draw_text.called
        # Multiple instruction lines
        assert mock_renderer.draw_text.call_count >= 5


class TestRunInteractiveCalibration:
    """Tests for run_interactive_calibration function."""

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_up_key_increases_aspect(self, mock_config_class, mock_renderer_class):
        """Test KEY_UP increases aspect ratio."""
        # Setup mock config
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        # Setup mock renderer
        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        # Mock keyboard input: UP key then ESC
        mock_key_up = MagicMock()
        mock_key_up.name = 'KEY_UP'
        mock_key_up.__eq__ = lambda self, other: False

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.lower.return_value = ''
        mock_key_esc.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_up, mock_key_esc]

        saved, final_value = run_interactive_calibration()

        # Aspect should have increased by ASPECT_INCREMENT
        assert final_value == 0.5 + ASPECT_INCREMENT
        assert not saved  # ESC cancels

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_down_key_decreases_aspect(self, mock_config_class, mock_renderer_class):
        """Test KEY_DOWN decreases aspect ratio."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_down = MagicMock()
        mock_key_down.name = 'KEY_DOWN'
        mock_key_down.__eq__ = lambda self, other: False

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.lower.return_value = ''
        mock_key_esc.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_down, mock_key_esc]

        saved, final_value = run_interactive_calibration()

        assert final_value == 0.5 - ASPECT_INCREMENT
        assert not saved

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_plus_key_increases_aspect(self, mock_config_class, mock_renderer_class):
        """Test + key increases aspect ratio."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        # + key (character comparison)
        mock_key_plus = MagicMock()
        mock_key_plus.name = None
        mock_key_plus.__eq__ = lambda self, other: other == '+'

        mock_key_q = MagicMock()
        mock_key_q.name = None
        mock_key_q.__eq__ = lambda self, other: False
        mock_key_q.lower.return_value = 'q'

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_plus, mock_key_q]

        saved, final_value = run_interactive_calibration()

        assert final_value == 0.5 + ASPECT_INCREMENT
        assert not saved

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_minus_key_decreases_aspect(self, mock_config_class, mock_renderer_class):
        """Test - key decreases aspect ratio."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_minus = MagicMock()
        mock_key_minus.name = None
        mock_key_minus.__eq__ = lambda self, other: other == '-'

        mock_key_q = MagicMock()
        mock_key_q.name = None
        mock_key_q.__eq__ = lambda self, other: False
        mock_key_q.lower.return_value = 'q'

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_minus, mock_key_q]

        saved, final_value = run_interactive_calibration()

        assert final_value == 0.5 - ASPECT_INCREMENT
        assert not saved

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_enter_key_saves_config(self, mock_config_class, mock_renderer_class):
        """Test ENTER key saves configuration."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_enter = MagicMock()
        mock_key_enter.name = 'KEY_ENTER'
        mock_key_enter.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_enter]

        saved, final_value = run_interactive_calibration()

        assert saved
        assert final_value == 0.5
        mock_config.save.assert_called_once()

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_escape_key_cancels(self, mock_config_class, mock_renderer_class):
        """Test ESC key cancels without saving."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.__eq__ = lambda self, other: False
        mock_key_esc.lower.return_value = ''

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_esc]

        saved, final_value = run_interactive_calibration()

        assert not saved
        mock_config.save.assert_not_called()

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_q_key_cancels(self, mock_config_class, mock_renderer_class):
        """Test Q key cancels without saving."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_q = MagicMock()
        mock_key_q.name = None
        mock_key_q.__eq__ = lambda self, other: False
        mock_key_q.lower.return_value = 'q'

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_q]

        saved, final_value = run_interactive_calibration()

        assert not saved
        mock_config.save.assert_not_called()

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_aspect_upper_bound(self, mock_config_class, mock_renderer_class):
        """Test aspect ratio is capped at MAX_ASPECT_RATIO."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.99  # Start near max
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        # Two UP keys should not exceed MAX_ASPECT_RATIO
        mock_key_up = MagicMock()
        mock_key_up.name = 'KEY_UP'
        mock_key_up.__eq__ = lambda self, other: False

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.lower.return_value = ''
        mock_key_esc.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_up, mock_key_up, mock_key_esc]

        saved, final_value = run_interactive_calibration()

        assert final_value <= MAX_ASPECT_RATIO
        assert not saved

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_aspect_lower_bound(self, mock_config_class, mock_renderer_class):
        """Test aspect ratio is floored at MIN_ASPECT_RATIO."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.11  # Start near min
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        # Two DOWN keys should not go below MIN_ASPECT_RATIO
        mock_key_down = MagicMock()
        mock_key_down.name = 'KEY_DOWN'
        mock_key_down.__eq__ = lambda self, other: False

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.lower.return_value = ''
        mock_key_esc.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_down, mock_key_down, mock_key_esc]

        saved, final_value = run_interactive_calibration()

        assert final_value >= MIN_ASPECT_RATIO
        assert not saved

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_enter_after_adjustment_saves_new_value(
        self, mock_config_class, mock_renderer_class
    ):
        """Test ENTER saves the adjusted value."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_up = MagicMock()
        mock_key_up.name = 'KEY_UP'
        mock_key_up.__eq__ = lambda self, other: False

        mock_key_enter = MagicMock()
        mock_key_enter.name = 'KEY_ENTER'
        mock_key_enter.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_up, mock_key_enter]

        saved, final_value = run_interactive_calibration()

        assert saved
        assert final_value == 0.5 + ASPECT_INCREMENT
        # Verify the saved value matches the adjusted value
        assert mock_config.char_aspect == 0.5 + ASPECT_INCREMENT
        mock_config.save.assert_called_once()

    @patch('atari_style.tools.aspect_calibration.Renderer')
    @patch('atari_style.tools.aspect_calibration.Config')
    def test_fullscreen_mode_lifecycle(self, mock_config_class, mock_renderer_class):
        """Test fullscreen mode is entered and exited properly."""
        mock_config = MagicMock()
        mock_config.char_aspect = 0.5
        mock_config_class.load.return_value = mock_config

        mock_renderer = MagicMock()
        mock_renderer.width = 80
        mock_renderer.height = 24
        mock_renderer_class.return_value = mock_renderer

        mock_key_esc = MagicMock()
        mock_key_esc.name = 'KEY_ESCAPE'
        mock_key_esc.lower.return_value = ''
        mock_key_esc.__eq__ = lambda self, other: False

        mock_renderer.term.cbreak.return_value.__enter__ = MagicMock()
        mock_renderer.term.cbreak.return_value.__exit__ = MagicMock()
        mock_renderer.term.inkey.side_effect = [mock_key_esc]

        run_interactive_calibration()

        mock_renderer.enter_fullscreen.assert_called_once()
        mock_renderer.exit_fullscreen.assert_called_once()


class TestConstants:
    """Tests for module constants."""

    def test_aspect_increment_is_small(self):
        """Test ASPECT_INCREMENT is a small reasonable value."""
        assert ASPECT_INCREMENT == 0.01
        assert ASPECT_INCREMENT > 0
        assert ASPECT_INCREMENT < MIN_ASPECT_RATIO
