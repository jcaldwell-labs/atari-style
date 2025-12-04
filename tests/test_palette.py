"""Tests for Palette class and Color constants."""

import unittest

from atari_style.core.renderer import Color, Palette


class TestColorConstants(unittest.TestCase):
    """Test Color class constants."""

    def test_standard_colors_defined(self):
        """Test that all standard colors are defined."""
        standard_colors = [
            Color.BLACK, Color.RED, Color.GREEN, Color.BLUE,
            Color.YELLOW, Color.MAGENTA, Color.CYAN, Color.WHITE,
        ]
        for color in standard_colors:
            self.assertIsInstance(color, str)
            self.assertTrue(len(color) > 0)

    def test_bright_colors_defined(self):
        """Test that all bright colors are defined."""
        bright_colors = [
            Color.BRIGHT_BLACK, Color.BRIGHT_RED, Color.BRIGHT_GREEN,
            Color.BRIGHT_BLUE, Color.BRIGHT_YELLOW, Color.BRIGHT_MAGENTA,
            Color.BRIGHT_CYAN, Color.BRIGHT_WHITE,
        ]
        for color in bright_colors:
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith('bright_'))

    def test_gray_alias(self):
        """Test that GRAY is an alias for BRIGHT_BLACK."""
        self.assertEqual(Color.GRAY, Color.BRIGHT_BLACK)


class TestPaletteClass(unittest.TestCase):
    """Test Palette class functionality."""

    def test_classic_palette_exists(self):
        """Test that CLASSIC palette is defined."""
        self.assertIsInstance(Palette.CLASSIC, list)
        self.assertTrue(len(Palette.CLASSIC) > 0)

    def test_plasma_palette_exists(self):
        """Test that PLASMA palette is defined."""
        self.assertIsInstance(Palette.PLASMA, list)
        self.assertTrue(len(Palette.PLASMA) > 0)

    def test_midnight_palette_exists(self):
        """Test that MIDNIGHT palette is defined."""
        self.assertIsInstance(Palette.MIDNIGHT, list)
        self.assertTrue(len(Palette.MIDNIGHT) > 0)

    def test_forest_palette_exists(self):
        """Test that FOREST palette is defined."""
        self.assertIsInstance(Palette.FOREST, list)
        self.assertTrue(len(Palette.FOREST) > 0)

    def test_fire_palette_exists(self):
        """Test that FIRE palette is defined."""
        self.assertIsInstance(Palette.FIRE, list)
        self.assertTrue(len(Palette.FIRE) > 0)

    def test_ocean_palette_exists(self):
        """Test that OCEAN palette is defined."""
        self.assertIsInstance(Palette.OCEAN, list)
        self.assertTrue(len(Palette.OCEAN) > 0)

    def test_monochrome_palette_exists(self):
        """Test that MONOCHROME palette is defined."""
        self.assertIsInstance(Palette.MONOCHROME, list)
        self.assertTrue(len(Palette.MONOCHROME) > 0)

    def test_all_dict_contains_all_palettes(self):
        """Test that ALL dict contains all named palettes."""
        expected_names = ['classic', 'plasma', 'midnight', 'forest', 'fire', 'ocean', 'monochrome']
        for name in expected_names:
            self.assertIn(name, Palette.ALL)
            self.assertIsInstance(Palette.ALL[name], list)

    def test_get_returns_named_palette(self):
        """Test that get() returns the correct palette by name."""
        self.assertEqual(Palette.get('classic'), Palette.CLASSIC)
        self.assertEqual(Palette.get('plasma'), Palette.PLASMA)
        self.assertEqual(Palette.get('fire'), Palette.FIRE)

    def test_get_is_case_insensitive(self):
        """Test that get() is case insensitive."""
        self.assertEqual(Palette.get('CLASSIC'), Palette.CLASSIC)
        self.assertEqual(Palette.get('Plasma'), Palette.PLASMA)
        self.assertEqual(Palette.get('MIDNIGHT'), Palette.MIDNIGHT)

    def test_get_returns_default_for_unknown(self):
        """Test that get() returns CLASSIC for unknown palette names."""
        self.assertEqual(Palette.get('nonexistent'), Palette.CLASSIC)
        self.assertEqual(Palette.get(''), Palette.CLASSIC)

    def test_palettes_contain_valid_colors(self):
        """Test that all palettes contain valid color strings."""
        valid_colors = {
            'black', 'red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_blue',
            'bright_yellow', 'bright_magenta', 'bright_cyan', 'bright_white',
        }
        for name, palette in Palette.ALL.items():
            for color in palette:
                self.assertIn(color, valid_colors,
                              f"Palette '{name}' contains invalid color: {color}")

    def test_palettes_have_multiple_colors(self):
        """Test that palettes have at least 3 colors for gradients."""
        for name, palette in Palette.ALL.items():
            self.assertGreaterEqual(len(palette), 3,
                                    f"Palette '{name}' should have at least 3 colors")


if __name__ == '__main__':
    unittest.main()
