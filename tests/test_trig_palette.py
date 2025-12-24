"""Tests for the trigonometric color palette system."""

import pytest
import math
from atari_style.core.trig_palette import (
    palette,
    palette_rgb,
    palette_to_list,
    interpolate_palettes,
    PaletteParams,
    PRESETS,
    get_preset,
    list_presets,
    to_terminal_256,
    palette_to_terminal_256,
    generate_glsl_function,
    generate_glsl_preset,
)


class TestPaletteFunction:
    """Tests for the core palette function."""

    def test_palette_returns_tuple(self):
        """Palette returns a 3-tuple."""
        result = palette(0.5)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_palette_values_in_range(self):
        """Palette values are clamped to 0.0-1.0."""
        for t in [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
            r, g, b = palette(t)
            assert 0.0 <= r <= 1.0
            assert 0.0 <= g <= 1.0
            assert 0.0 <= b <= 1.0

    def test_palette_at_zero(self):
        """Palette at t=0 uses default parameters correctly."""
        r, g, b = palette(0.0)
        # With defaults: a + b * cos(2π * d)
        # For r: 0.5 + 0.5 * cos(0) = 0.5 + 0.5 = 1.0
        assert r == pytest.approx(1.0, abs=0.01)

    def test_palette_cyclic(self):
        """Palette cycles: t=0 and t=1 produce similar colors."""
        c0 = palette(0.0)
        c1 = palette(1.0)
        # Should be approximately equal (may differ due to phase)
        for i in range(3):
            assert c0[i] == pytest.approx(c1[i], abs=0.01)

    def test_palette_custom_params(self):
        """Palette accepts custom parameters."""
        # All black (a=0, b=0)
        r, g, b = palette(0.5, a=(0, 0, 0), b=(0, 0, 0), c=(1, 1, 1), d=(0, 0, 0))
        assert r == 0.0
        assert g == 0.0
        assert b == 0.0

        # All white (a=1, b=0)
        r, g, b = palette(0.5, a=(1, 1, 1), b=(0, 0, 0), c=(1, 1, 1), d=(0, 0, 0))
        assert r == 1.0
        assert g == 1.0
        assert b == 1.0

    def test_palette_grayscale(self):
        """Grayscale preset produces equal RGB values."""
        params = PRESETS['grayscale']
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            r, g, b = palette(t, **params)
            assert r == pytest.approx(g, abs=0.01)
            assert g == pytest.approx(b, abs=0.01)


class TestPaletteRgb:
    """Tests for palette_rgb function."""

    def test_palette_rgb_returns_integers(self):
        """palette_rgb returns integer tuple."""
        r, g, b = palette_rgb(0.5)
        assert isinstance(r, int)
        assert isinstance(g, int)
        assert isinstance(b, int)

    def test_palette_rgb_range(self):
        """palette_rgb values are in 0-255 range."""
        for t in [0.0, 0.5, 1.0]:
            r, g, b = palette_rgb(t)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


class TestPaletteToList:
    """Tests for palette_to_list function."""

    def test_palette_to_list_length(self):
        """palette_to_list returns correct number of colors."""
        colors = palette_to_list(10)
        assert len(colors) == 10

        colors = palette_to_list(256)
        assert len(colors) == 256

    def test_palette_to_list_as_int(self):
        """palette_to_list with as_int=True returns integers."""
        colors = palette_to_list(5, as_int=True)
        for r, g, b in colors:
            assert isinstance(r, int)
            assert isinstance(g, int)
            assert isinstance(b, int)

    def test_palette_to_list_as_float(self):
        """palette_to_list with as_int=False returns floats."""
        colors = palette_to_list(5, as_int=False)
        for r, g, b in colors:
            assert isinstance(r, float)
            assert isinstance(g, float)
            assert isinstance(b, float)


class TestPresets:
    """Tests for preset palettes."""

    def test_all_presets_exist(self):
        """All documented presets exist."""
        expected = [
            'rainbow', 'sunset', 'ocean', 'fire', 'neon',
            'pastel', 'forest', 'cyberpunk', 'grayscale',
            'heat', 'ice', 'lava'
        ]
        for name in expected:
            assert name in PRESETS

    def test_presets_have_required_keys(self):
        """All presets have a, b, c, d parameters."""
        for name, params in PRESETS.items():
            assert 'a' in params, f"{name} missing 'a'"
            assert 'b' in params, f"{name} missing 'b'"
            assert 'c' in params, f"{name} missing 'c'"
            assert 'd' in params, f"{name} missing 'd'"

    def test_preset_values_are_vec3(self):
        """All preset values are 3-tuples."""
        for name, params in PRESETS.items():
            for key in ['a', 'b', 'c', 'd']:
                assert len(params[key]) == 3, f"{name}.{key} is not vec3"

    def test_get_preset(self):
        """get_preset returns PaletteParams."""
        params = get_preset('rainbow')
        assert isinstance(params, PaletteParams)
        assert params.a == PRESETS['rainbow']['a']

    def test_get_preset_invalid(self):
        """get_preset raises KeyError for invalid name."""
        with pytest.raises(KeyError):
            get_preset('nonexistent')

    def test_list_presets(self):
        """list_presets returns all preset names."""
        names = list_presets()
        assert 'rainbow' in names
        assert len(names) == len(PRESETS)


class TestInterpolation:
    """Tests for palette interpolation."""

    def test_interpolate_at_zero(self):
        """Interpolation at mix=0 returns first palette."""
        p1 = PaletteParams(a=(1, 0, 0), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))
        p2 = PaletteParams(a=(0, 0, 1), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))

        color = interpolate_palettes(0.5, p1, p2, 0.0)
        assert color[0] == pytest.approx(1.0, abs=0.01)
        assert color[2] == pytest.approx(0.0, abs=0.01)

    def test_interpolate_at_one(self):
        """Interpolation at mix=1 returns second palette."""
        p1 = PaletteParams(a=(1, 0, 0), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))
        p2 = PaletteParams(a=(0, 0, 1), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))

        color = interpolate_palettes(0.5, p1, p2, 1.0)
        assert color[0] == pytest.approx(0.0, abs=0.01)
        assert color[2] == pytest.approx(1.0, abs=0.01)

    def test_interpolate_midpoint(self):
        """Interpolation at mix=0.5 blends both palettes."""
        p1 = PaletteParams(a=(1, 0, 0), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))
        p2 = PaletteParams(a=(0, 0, 1), b=(0, 0, 0), c=(0, 0, 0), d=(0, 0, 0))

        color = interpolate_palettes(0.5, p1, p2, 0.5)
        assert color[0] == pytest.approx(0.5, abs=0.01)
        assert color[2] == pytest.approx(0.5, abs=0.01)


class TestTerminal256:
    """Tests for terminal 256-color mapping."""

    def test_to_terminal_256_black(self):
        """Black maps to color 16."""
        assert to_terminal_256((0.0, 0.0, 0.0)) == 16

    def test_to_terminal_256_white(self):
        """White maps to color 231."""
        assert to_terminal_256((1.0, 1.0, 1.0)) == 231

    def test_to_terminal_256_range(self):
        """All results are in valid range."""
        for t in [i / 100 for i in range(101)]:
            color = palette(t)
            idx = to_terminal_256(color)
            assert 0 <= idx <= 255

    def test_palette_to_terminal_256_length(self):
        """palette_to_terminal_256 returns correct length."""
        result = palette_to_terminal_256(32)
        assert len(result) == 32


class TestGlslGeneration:
    """Tests for GLSL code generation."""

    def test_generate_glsl_function(self):
        """GLSL function generation produces valid code."""
        code = generate_glsl_function()
        assert 'vec3 trig_palette' in code
        assert 'cos(' in code
        assert '6.28318' in code

    def test_generate_glsl_preset(self):
        """GLSL preset generation produces constants."""
        code = generate_glsl_preset('rainbow')
        assert 'RAINBOW_A' in code
        assert 'RAINBOW_B' in code
        assert 'RAINBOW_C' in code
        assert 'RAINBOW_D' in code
        assert 'vec3(' in code

    def test_generate_glsl_preset_invalid(self):
        """GLSL preset raises KeyError for invalid name."""
        with pytest.raises(KeyError):
            generate_glsl_preset('nonexistent')


class TestPaletteParams:
    """Tests for PaletteParams dataclass."""

    def test_palette_params_to_dict(self):
        """PaletteParams.to_dict returns usable dictionary."""
        params = PaletteParams(
            a=(0.5, 0.5, 0.5),
            b=(0.5, 0.5, 0.5),
            c=(1.0, 1.0, 1.0),
            d=(0.0, 0.33, 0.67)
        )
        d = params.to_dict()
        assert 'a' in d
        assert 'b' in d
        assert 'c' in d
        assert 'd' in d

        # Should be usable with palette()
        color = palette(0.5, **d)
        assert len(color) == 3
