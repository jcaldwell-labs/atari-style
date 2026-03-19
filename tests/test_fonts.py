"""Tests for the shared font loading utility."""

import logging
import unittest
from unittest.mock import patch, MagicMock

from atari_style.utils.fonts import load_monospace_font, DEFAULT_FONT_PATHS


class TestLoadMonospaceFont(unittest.TestCase):
    """Tests for load_monospace_font()."""

    @patch("atari_style.utils.fonts.ImageFont")
    def test_loads_first_available_default_path(self, mock_image_font):
        """Should return a TrueType font from the first working default path."""
        sentinel = MagicMock(name="truetype_font")
        mock_image_font.truetype.return_value = sentinel

        result = load_monospace_font(22)

        mock_image_font.truetype.assert_called_once_with(DEFAULT_FONT_PATHS[0], 22)
        self.assertIs(result, sentinel)

    @patch("atari_style.utils.fonts.ImageFont")
    def test_tries_paths_in_order(self, mock_image_font):
        """Should skip paths that raise OSError and try the next."""
        sentinel = MagicMock(name="truetype_font")
        mock_image_font.truetype.side_effect = [OSError, OSError, sentinel]

        result = load_monospace_font(16)

        self.assertIs(result, sentinel)
        self.assertEqual(mock_image_font.truetype.call_count, 3)

    @patch("atari_style.utils.fonts.ImageFont")
    def test_fallback_to_default_when_no_paths_work(self, mock_image_font):
        """Should fall back to load_default() when all truetype paths fail."""
        mock_image_font.truetype.side_effect = OSError
        default_font = MagicMock(name="default_font")
        mock_image_font.load_default.return_value = default_font

        result = load_monospace_font(20)

        mock_image_font.load_default.assert_called_once()
        self.assertIs(result, default_font)

    @patch("atari_style.utils.fonts.ImageFont")
    def test_custom_preferred_paths_tried_first(self, mock_image_font):
        """Should try preferred_paths before DEFAULT_FONT_PATHS."""
        sentinel = MagicMock(name="truetype_font")
        mock_image_font.truetype.side_effect = [OSError, sentinel]
        custom_paths = ["/nonexistent/font.ttf", "/my/custom/font.ttf"]

        result = load_monospace_font(18, preferred_paths=custom_paths)

        self.assertIs(result, sentinel)
        # Second call should be the second custom path
        self.assertEqual(
            mock_image_font.truetype.call_args_list[1][0],
            ("/my/custom/font.ttf", 18),
        )

    @patch("atari_style.utils.fonts.ImageFont")
    def test_logs_warning_on_fallback(self, mock_image_font):
        """Should log a warning when falling back to the default font."""
        mock_image_font.truetype.side_effect = OSError
        mock_image_font.load_default.return_value = MagicMock()

        with self.assertLogs("atari_style.utils.fonts", level=logging.WARNING) as cm:
            load_monospace_font(20)

        self.assertTrue(any("fallback" in msg.lower() or "falling back" in msg.lower()
                            for msg in cm.output))

    @patch("atari_style.utils.fonts.ImageFont")
    def test_no_warning_when_font_found(self, mock_image_font):
        """Should not log a warning when a TrueType font is successfully loaded."""
        mock_image_font.truetype.return_value = MagicMock()

        with self.assertNoLogs("atari_style.utils.fonts", level=logging.WARNING):
            load_monospace_font(22)


if __name__ == "__main__":
    unittest.main()
