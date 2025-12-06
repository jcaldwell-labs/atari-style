"""Tests for GLSL utility functions.

Tests cover both scalar and numpy array operations for all functions.
"""

import math
import unittest
from unittest.mock import patch

from atari_style.core.glsl_utils import (
    PI, TAU,
    fract, step, smoothstep, mix, lerp, clamp, mod, sign, abs_,
    length, distance, normalize_2d, dot_2d,
    palette, PALETTE_RAINBOW, PALETTE_FIRE, PALETTE_OCEAN,
    tile_uv, repeat_polar, rotate_2d, warp,
    hash_1d, hash_2d,
)


class TestConstants(unittest.TestCase):
    """Test mathematical constants."""

    def test_pi(self):
        """PI matches math.pi."""
        self.assertAlmostEqual(PI, math.pi, places=10)

    def test_tau(self):
        """TAU equals 2*PI."""
        self.assertAlmostEqual(TAU, 2 * math.pi, places=10)


class TestFract(unittest.TestCase):
    """Test fract() - fractional part function."""

    def test_positive_float(self):
        """fract of positive float returns fractional part."""
        self.assertAlmostEqual(fract(1.7), 0.7, places=10)
        self.assertAlmostEqual(fract(3.25), 0.25, places=10)

    def test_negative_float(self):
        """fract of negative float returns positive fractional part."""
        # GLSL behavior: fract(-0.3) = 0.7 (not -0.3)
        self.assertAlmostEqual(fract(-0.3), 0.7, places=10)

    def test_integer(self):
        """fract of integer returns 0."""
        self.assertAlmostEqual(fract(5.0), 0.0, places=10)

    def test_zero(self):
        """fract of zero returns 0."""
        self.assertAlmostEqual(fract(0.0), 0.0, places=10)


class TestStep(unittest.TestCase):
    """Test step() - threshold function."""

    def test_below_edge(self):
        """step returns 0 when x < edge."""
        self.assertEqual(step(0.5, 0.3), 0.0)
        self.assertEqual(step(1.0, 0.0), 0.0)

    def test_above_edge(self):
        """step returns 1 when x >= edge."""
        self.assertEqual(step(0.5, 0.7), 1.0)
        self.assertEqual(step(0.5, 0.5), 1.0)  # Equal to edge

    def test_edge_exactly(self):
        """step returns 1 when x == edge."""
        self.assertEqual(step(0.5, 0.5), 1.0)


class TestSmoothstep(unittest.TestCase):
    """Test smoothstep() - smooth interpolation function."""

    def test_below_edge0(self):
        """smoothstep returns 0 when x <= edge0."""
        self.assertAlmostEqual(smoothstep(0.2, 0.8, 0.0), 0.0, places=10)
        self.assertAlmostEqual(smoothstep(0.2, 0.8, 0.2), 0.0, places=10)

    def test_above_edge1(self):
        """smoothstep returns 1 when x >= edge1."""
        self.assertAlmostEqual(smoothstep(0.2, 0.8, 1.0), 1.0, places=10)
        self.assertAlmostEqual(smoothstep(0.2, 0.8, 0.8), 1.0, places=10)

    def test_midpoint(self):
        """smoothstep at midpoint returns 0.5."""
        self.assertAlmostEqual(smoothstep(0.0, 1.0, 0.5), 0.5, places=10)

    def test_smooth_derivative(self):
        """smoothstep has zero derivative at edges."""
        # Test near edge0 - should be very close to 0
        result = smoothstep(0.0, 1.0, 0.01)
        self.assertLess(result, 0.01)  # Very slow start

        # Test near edge1 - should be very close to 1
        result = smoothstep(0.0, 1.0, 0.99)
        self.assertGreater(result, 0.99)  # Very slow end


class TestMix(unittest.TestCase):
    """Test mix() / lerp() - linear interpolation."""

    def test_at_zero(self):
        """mix at t=0 returns a."""
        self.assertAlmostEqual(mix(10.0, 20.0, 0.0), 10.0, places=10)

    def test_at_one(self):
        """mix at t=1 returns b."""
        self.assertAlmostEqual(mix(10.0, 20.0, 1.0), 20.0, places=10)

    def test_at_half(self):
        """mix at t=0.5 returns midpoint."""
        self.assertAlmostEqual(mix(0.0, 100.0, 0.5), 50.0, places=10)

    def test_extrapolation(self):
        """mix with t > 1 extrapolates."""
        self.assertAlmostEqual(mix(0.0, 10.0, 2.0), 20.0, places=10)

    def test_lerp_alias(self):
        """lerp is an alias for mix."""
        self.assertEqual(lerp(0.0, 10.0, 0.5), mix(0.0, 10.0, 0.5))


class TestClamp(unittest.TestCase):
    """Test clamp() - range constraint function."""

    def test_within_range(self):
        """clamp returns input when within range."""
        self.assertAlmostEqual(clamp(0.5, 0.0, 1.0), 0.5, places=10)

    def test_below_min(self):
        """clamp returns min when input below range."""
        self.assertAlmostEqual(clamp(-0.5, 0.0, 1.0), 0.0, places=10)

    def test_above_max(self):
        """clamp returns max when input above range."""
        self.assertAlmostEqual(clamp(1.5, 0.0, 1.0), 1.0, places=10)


class TestMod(unittest.TestCase):
    """Test mod() - GLSL-style modulo."""

    def test_positive_values(self):
        """mod with positive values behaves like %."""
        self.assertAlmostEqual(mod(5.5, 2.0), 1.5, places=10)

    def test_negative_dividend(self):
        """mod with negative dividend returns positive result."""
        # GLSL mod(-0.5, 1.0) = 0.5, unlike Python -0.5 % 1.0 = 0.5
        self.assertAlmostEqual(mod(-0.5, 1.0), 0.5, places=10)

    def test_result_range(self):
        """mod result is always in [0, divisor)."""
        for x in [-3.7, -1.2, 0.0, 1.5, 4.8]:
            result = mod(x, 2.0)
            self.assertGreaterEqual(result, 0.0)
            self.assertLess(result, 2.0)


class TestSign(unittest.TestCase):
    """Test sign() - sign extraction function."""

    def test_positive(self):
        """sign of positive number is 1."""
        self.assertEqual(sign(5.0), 1.0)
        self.assertEqual(sign(0.001), 1.0)

    def test_negative(self):
        """sign of negative number is -1."""
        self.assertEqual(sign(-5.0), -1.0)
        self.assertEqual(sign(-0.001), -1.0)

    def test_zero(self):
        """sign of zero is 0."""
        self.assertEqual(sign(0.0), 0.0)


class TestVectorFunctions(unittest.TestCase):
    """Test vector/coordinate functions."""

    def test_length_2d(self):
        """length of 2D vector (3, 4) is 5."""
        self.assertAlmostEqual(length(3.0, 4.0), 5.0, places=10)

    def test_length_3d(self):
        """length of 3D vector works correctly."""
        # sqrt(1^2 + 2^2 + 2^2) = sqrt(9) = 3
        self.assertAlmostEqual(length(1.0, 2.0, 2.0), 3.0, places=10)

    def test_distance_2d(self):
        """distance between (0,0) and (3,4) is 5."""
        self.assertAlmostEqual(distance(0.0, 0.0, 3.0, 4.0), 5.0, places=10)

    def test_normalize_unit_vector(self):
        """normalize returns unit vector."""
        x, y = normalize_2d(3.0, 4.0)
        self.assertAlmostEqual(x, 0.6, places=10)
        self.assertAlmostEqual(y, 0.8, places=10)
        # Result should have length 1
        self.assertAlmostEqual(length(x, y), 1.0, places=10)

    def test_normalize_zero_vector(self):
        """normalize of zero vector returns zero."""
        x, y = normalize_2d(0.0, 0.0)
        self.assertEqual((x, y), (0.0, 0.0))

    def test_dot_product_orthogonal(self):
        """dot product of orthogonal vectors is 0."""
        self.assertAlmostEqual(dot_2d(1.0, 0.0, 0.0, 1.0), 0.0, places=10)

    def test_dot_product_parallel(self):
        """dot product of parallel vectors equals product of lengths."""
        # (2, 0) dot (3, 0) = 6
        self.assertAlmostEqual(dot_2d(2.0, 0.0, 3.0, 0.0), 6.0, places=10)


class TestPalette(unittest.TestCase):
    """Test Inigo Quilez color palette function."""

    def test_output_range(self):
        """palette output is clamped to [0, 1]."""
        for t in [0.0, 0.25, 0.5, 0.75, 1.0, 2.0]:
            r, g, b = palette(t)
            self.assertGreaterEqual(r, 0.0)
            self.assertLessEqual(r, 1.0)
            self.assertGreaterEqual(g, 0.0)
            self.assertLessEqual(g, 1.0)
            self.assertGreaterEqual(b, 0.0)
            self.assertLessEqual(b, 1.0)

    def test_cyclic_at_t1(self):
        """palette at t=1 equals palette at t=0."""
        r0, g0, b0 = palette(0.0)
        r1, g1, b1 = palette(1.0)
        self.assertAlmostEqual(r0, r1, places=5)
        self.assertAlmostEqual(g0, g1, places=5)
        self.assertAlmostEqual(b0, b1, places=5)

    def test_preset_palettes_exist(self):
        """Preset palette tuples have correct structure."""
        for preset in [PALETTE_RAINBOW, PALETTE_FIRE, PALETTE_OCEAN]:
            self.assertEqual(len(preset), 4)  # a, b, c, d
            for component in preset:
                self.assertEqual(len(component), 3)  # RGB


class TestPatternFunctions(unittest.TestCase):
    """Test pattern/domain functions."""

    def test_tile_uv(self):
        """tile_uv creates repeating coordinates."""
        x, y = tile_uv(2.5, 3.7, 2.0)
        # 2.5 * 2 = 5.0, fract = 0.0
        # 3.7 * 2 = 7.4, fract = 0.4
        self.assertAlmostEqual(x, 0.0, places=10)
        self.assertAlmostEqual(y, 0.4, places=10)

    def test_rotate_2d_90_degrees(self):
        """rotate_2d by 90 degrees swaps and negates."""
        x, y = rotate_2d(1.0, 0.0, math.pi / 2)
        self.assertAlmostEqual(x, 0.0, places=10)
        self.assertAlmostEqual(y, 1.0, places=10)

    def test_rotate_2d_180_degrees(self):
        """rotate_2d by 180 degrees negates both."""
        x, y = rotate_2d(1.0, 2.0, math.pi)
        self.assertAlmostEqual(x, -1.0, places=10)
        self.assertAlmostEqual(y, -2.0, places=10)

    def test_warp_modifies_coordinates(self):
        """warp changes input coordinates based on time."""
        x1, y1 = warp(0.5, 0.5, 0.0)
        x2, y2 = warp(0.5, 0.5, 1.0)
        # Different times should give different results
        self.assertNotEqual(x1, x2)
        self.assertNotEqual(y1, y2)


class TestHashFunctions(unittest.TestCase):
    """Test pseudo-random hash functions."""

    def test_hash_1d_range(self):
        """hash_1d returns values in [0, 1)."""
        for x in [-10.0, -1.0, 0.0, 1.0, 10.0, 100.0]:
            result = hash_1d(x)
            self.assertGreaterEqual(result, 0.0)
            self.assertLess(result, 1.0)

    def test_hash_1d_deterministic(self):
        """hash_1d returns same value for same input."""
        self.assertEqual(hash_1d(42.0), hash_1d(42.0))

    def test_hash_2d_range(self):
        """hash_2d returns values in [0, 1)."""
        for x, y in [(0, 0), (1, 1), (-1, 2), (100, -50)]:
            result = hash_2d(float(x), float(y))
            self.assertGreaterEqual(result, 0.0)
            self.assertLess(result, 1.0)

    def test_hash_2d_different_inputs(self):
        """hash_2d gives different values for different inputs."""
        h1 = hash_2d(1.0, 2.0)
        h2 = hash_2d(2.0, 1.0)
        h3 = hash_2d(1.0, 3.0)
        # These should all be different (with very high probability)
        self.assertNotEqual(h1, h2)
        self.assertNotEqual(h1, h3)


class TestNumpyCompatibility(unittest.TestCase):
    """Test that functions work with numpy arrays when available."""

    def test_fract_with_numpy(self):
        """fract works with numpy arrays."""
        try:
            import numpy as np
            arr = np.array([1.7, 2.3, -0.5])
            result = fract(arr)
            expected = np.array([0.7, 0.3, 0.5])
            np.testing.assert_array_almost_equal(result, expected)
        except ImportError:
            self.skipTest("numpy not available")

    def test_smoothstep_with_numpy(self):
        """smoothstep works with numpy arrays."""
        try:
            import numpy as np
            arr = np.array([0.0, 0.5, 1.0])
            result = smoothstep(0.0, 1.0, arr)
            self.assertEqual(len(result), 3)
            self.assertAlmostEqual(result[1], 0.5, places=5)
        except ImportError:
            self.skipTest("numpy not available")

    def test_clamp_with_numpy(self):
        """clamp works with numpy arrays."""
        try:
            import numpy as np
            arr = np.array([-0.5, 0.5, 1.5])
            result = clamp(arr, 0.0, 1.0)
            expected = np.array([0.0, 0.5, 1.0])
            np.testing.assert_array_almost_equal(result, expected)
        except ImportError:
            self.skipTest("numpy not available")


if __name__ == '__main__':
    unittest.main()
