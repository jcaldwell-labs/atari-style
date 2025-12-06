"""Tests for aspect calibration CLI and config module."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from atari_style.core.config import (
    Config,
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_CHAR_ASPECT,
)
from atari_style.tools.aspect_calibration import (
    draw_circle,
    draw_crosshairs,
    draw_instructions,
    show_current_value,
    reset_to_default,
    main,
    ASPECT_INCREMENT,
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
        # Aspect ratio should be between 0.1 and 1.0
        assert 0.1 <= data['char_aspect'] <= 1.0


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


class TestConstants:
    """Tests for module constants."""

    def test_aspect_increment_is_small(self):
        """Test ASPECT_INCREMENT is a small reasonable value."""
        assert ASPECT_INCREMENT == 0.01
        assert ASPECT_INCREMENT > 0
        assert ASPECT_INCREMENT < 0.1
