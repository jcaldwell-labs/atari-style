"""Tests for atari_style.core.config module."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from atari_style.core.config import (
    CHAR_ASPECT_MAX,
    CHAR_ASPECT_MIN,
    DEFAULT_CHAR_ASPECT,
    Config,
)


class TestConfigDefaults(unittest.TestCase):
    """Tests for Config default values."""

    def test_default_char_aspect(self):
        config = Config()
        self.assertEqual(config.char_aspect, DEFAULT_CHAR_ASPECT)

    def test_valid_char_aspect(self):
        config = Config(char_aspect=0.55)
        self.assertEqual(config.char_aspect, 0.55)

    def test_boundary_min(self):
        config = Config(char_aspect=CHAR_ASPECT_MIN)
        self.assertEqual(config.char_aspect, CHAR_ASPECT_MIN)

    def test_boundary_max(self):
        config = Config(char_aspect=CHAR_ASPECT_MAX)
        self.assertEqual(config.char_aspect, CHAR_ASPECT_MAX)

    def test_int_accepted(self):
        """Integer values within range should be accepted."""
        config = Config(char_aspect=1)
        self.assertEqual(config.char_aspect, 1)


class TestConfigValidation(unittest.TestCase):
    """Tests for Config __post_init__ validation."""

    def test_char_aspect_below_min(self):
        with self.assertRaises(ValueError) as ctx:
            Config(char_aspect=0.1)
        self.assertIn("0.2", str(ctx.exception))

    def test_char_aspect_above_max(self):
        with self.assertRaises(ValueError) as ctx:
            Config(char_aspect=2.0)
        self.assertIn("1.0", str(ctx.exception))

    def test_char_aspect_negative(self):
        with self.assertRaises(ValueError):
            Config(char_aspect=-0.5)

    def test_char_aspect_zero(self):
        with self.assertRaises(ValueError):
            Config(char_aspect=0.0)

    def test_char_aspect_wrong_type(self):
        with self.assertRaises(TypeError) as ctx:
            Config(char_aspect="0.5")
        self.assertIn("str", str(ctx.exception))


class TestConfigLoad(unittest.TestCase):
    """Tests for Config.load() with validation."""

    def test_load_returns_defaults_for_invalid_range(self):
        """Config file with out-of-range values should fall back to defaults."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({"char_aspect": 5.0}, f)
            f.flush()
            config_path = Path(f.name)

        try:
            with patch("atari_style.core.config.CONFIG_FILE", config_path):
                config = Config.load()
            self.assertEqual(config.char_aspect, DEFAULT_CHAR_ASPECT)
        finally:
            config_path.unlink()

    def test_load_returns_defaults_for_invalid_type(self):
        """Config file with wrong type should fall back to defaults."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({"char_aspect": "bad"}, f)
            f.flush()
            config_path = Path(f.name)

        try:
            with patch("atari_style.core.config.CONFIG_FILE", config_path):
                config = Config.load()
            self.assertEqual(config.char_aspect, DEFAULT_CHAR_ASPECT)
        finally:
            config_path.unlink()

    def test_load_valid_config(self):
        """Config file with valid values should load correctly."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({"char_aspect": 0.55}, f)
            f.flush()
            config_path = Path(f.name)

        try:
            with patch("atari_style.core.config.CONFIG_FILE", config_path):
                config = Config.load()
            self.assertEqual(config.char_aspect, 0.55)
        finally:
            config_path.unlink()


if __name__ == "__main__":
    unittest.main()
