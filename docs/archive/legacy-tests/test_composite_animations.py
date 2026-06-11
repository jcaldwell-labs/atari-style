#!/usr/bin/env python3
"""Test composite animations and modulation system."""

import unittest
import math
from atari_style.demos.visualizers.screensaver import (
    PlasmaAnimation,
    LissajousCurve,
    FluidLattice,
    PlasmaLissajous,
    FluxSpiral,
    LissajousPlasma,
)
from atari_style.core.renderer import Renderer


class TestModulationInterface(unittest.TestCase):
    """Test the modulation interface on parametric animations."""
    
    def setUp(self):
        """Set up test renderer."""
        self.renderer = Renderer()
    
    def test_plasma_value_at_range(self):
        """Test that plasma values are in [-1, 1] range."""
        plasma = PlasmaAnimation(self.renderer)
        
        # Test various positions
        for x in range(0, self.renderer.width, 10):
            for y in range(0, self.renderer.height, 10):
                value = plasma.get_value_at(x, y, 0.0)
                self.assertGreaterEqual(value, -1.0, 
                    f"Plasma value {value} at ({x}, {y}) below -1.0")
                self.assertLessEqual(value, 1.0,
                    f"Plasma value {value} at ({x}, {y}) above 1.0")
    
    def test_plasma_global_value_range(self):
        """Test that plasma global value is in [-1, 1] range."""
        plasma = PlasmaAnimation(self.renderer)
        
        for t in [0.0, 1.0, 5.0, 10.0]:
            value = plasma.get_global_value(t)
            self.assertGreaterEqual(value, -1.0,
                f"Plasma global value {value} at t={t} below -1.0")
            self.assertLessEqual(value, 1.0,
                f"Plasma global value {value} at t={t} above 1.0")
    
    def test_lissajous_value_at_range(self):
        """Test that Lissajous values are in [-1, 1] range."""
        lissajous = LissajousCurve(self.renderer)
        
        # Test various positions
        for x in range(0, self.renderer.width, 20):
            for y in range(0, self.renderer.height, 20):
                value = lissajous.get_value_at(x, y, 0.0)
                self.assertGreaterEqual(value, -1.0,
                    f"Lissajous value {value} at ({x}, {y}) below -1.0")
                self.assertLessEqual(value, 1.0,
                    f"Lissajous value {value} at ({x}, {y}) above 1.0")
    
    def test_lissajous_global_value_range(self):
        """Test that Lissajous global value is in [-1, 1] range."""
        lissajous = LissajousCurve(self.renderer)
        
        for t in [0.0, 1.0, 5.0, 10.0]:
            value = lissajous.get_global_value(t)
            self.assertGreaterEqual(value, -1.0,
                f"Lissajous global value {value} at t={t} below -1.0")
            self.assertLessEqual(value, 1.0,
                f"Lissajous global value {value} at t={t} above 1.0")
    
    def test_flux_value_at_range(self):
        """Test that fluid lattice values are in [-1, 1] range."""
        flux = FluidLattice(self.renderer)
        
        # Initialize with some activity
        flux.update(0.1)
        
        # Test various positions
        for x in range(0, self.renderer.width, 20):
            for y in range(0, self.renderer.height, 20):
                value = flux.get_value_at(x, y, 0.0)
                self.assertGreaterEqual(value, -1.0,
                    f"Flux value {value} at ({x}, {y}) below -1.0")
                self.assertLessEqual(value, 1.0,
                    f"Flux value {value} at ({x}, {y}) above 1.0")
    
    def test_flux_global_value_range(self):
        """Test that fluid lattice global value is in [-1, 1] range."""
        flux = FluidLattice(self.renderer)
        
        # Run some updates to generate activity
        for _ in range(10):
            flux.update(0.1)
        
        value = flux.get_global_value(0.0)
        self.assertGreaterEqual(value, -1.0,
            f"Flux global value {value} below -1.0")
        self.assertLessEqual(value, 1.0,
            f"Flux global value {value} above 1.0")


class TestCompositeAnimation(unittest.TestCase):
    """Test composite animation functionality."""
    
    def setUp(self):
        """Set up test renderer."""
        self.renderer = Renderer()
    
    def test_composite_initialization(self):
        """Test that composites initialize correctly."""
        plasma_liss = PlasmaLissajous(self.renderer)
        self.assertIsNotNone(plasma_liss.source)
        self.assertIsNotNone(plasma_liss.target)
        self.assertEqual(plasma_liss.modulation_strength, 1.0)
        
        flux_spiral = FluxSpiral(self.renderer)
        self.assertIsNotNone(flux_spiral.source)
        self.assertIsNotNone(flux_spiral.target)
        
        liss_plasma = LissajousPlasma(self.renderer)
        self.assertIsNotNone(liss_plasma.source)
        self.assertIsNotNone(liss_plasma.target)
    
    def test_map_value_linear(self):
        """Test linear value mapping."""
        composite = PlasmaLissajous(self.renderer)
        composite.modulation_mapping = "linear"
        
        # Test mapping from [-1, 1] to [2, 6]
        self.assertAlmostEqual(composite.map_value(-1.0, 2.0, 6.0), 2.0, places=5)
        self.assertAlmostEqual(composite.map_value(0.0, 2.0, 6.0), 4.0, places=5)
        self.assertAlmostEqual(composite.map_value(1.0, 2.0, 6.0), 6.0, places=5)
    
    def test_map_value_quadratic(self):
        """Test quadratic value mapping."""
        composite = PlasmaLissajous(self.renderer)
        composite.modulation_mapping = "quadratic"
        
        # Test endpoints
        self.assertAlmostEqual(composite.map_value(-1.0, 2.0, 6.0), 2.0, places=5)
        self.assertAlmostEqual(composite.map_value(1.0, 2.0, 6.0), 6.0, places=5)
        
        # Middle should be less than linear midpoint (easing)
        result = composite.map_value(0.0, 2.0, 6.0)
        self.assertLess(result, 4.0)
        self.assertGreater(result, 2.0)
    
    def test_map_value_sine(self):
        """Test sinusoidal value mapping."""
        composite = PlasmaLissajous(self.renderer)
        composite.modulation_mapping = "sine"
        
        # Test endpoints
        self.assertAlmostEqual(composite.map_value(-1.0, 2.0, 6.0), 2.0, places=5)
        self.assertAlmostEqual(composite.map_value(1.0, 2.0, 6.0), 6.0, places=5)
    
    def test_modulation_strength(self):
        """Test that modulation strength affects output."""
        composite = PlasmaLissajous(self.renderer)
        composite.modulation_mapping = "linear"
        
        # Full strength
        composite.modulation_strength = 1.0
        full = composite.map_value(0.5, 2.0, 6.0)
        
        # Half strength
        composite.modulation_strength = 0.5
        half = composite.map_value(0.5, 2.0, 6.0)
        
        # Half strength should be closer to midpoint
        midpoint = 4.0
        self.assertLess(abs(half - midpoint), abs(full - midpoint))
    
    def test_plasma_lissajous_modulation(self):
        """Test that PlasmaLissajous modulates Lissajous frequencies."""
        composite = PlasmaLissajous(self.renderer)
        
        # Store initial frequency
        initial_a = composite.target.a
        
        # Draw with different times to get different plasma values
        composite.draw(0.0)
        freq_at_t0 = composite.target.a
        
        composite.draw(5.0)
        freq_at_t5 = composite.target.a
        
        # Frequencies should be modulated (different from initial and each other)
        # Due to plasma oscillation, they should vary
        self.assertTrue(
            freq_at_t0 != freq_at_t5 or freq_at_t0 != initial_a,
            "Lissajous frequencies should be modulated by plasma"
        )
    
    def test_flux_spiral_modulation(self):
        """Test that FluxSpiral modulates spiral rotation."""
        composite = FluxSpiral(self.renderer)
        
        # Generate some wave activity
        for _ in range(5):
            composite.source.update(0.1)
        
        # Draw and check rotation speed is set
        composite.draw(0.0)
        speed_1 = composite.target.rotation_speed
        
        # Add more wave activity
        for _ in range(10):
            composite.source.update(0.1)
        
        composite.draw(1.0)
        speed_2 = composite.target.rotation_speed
        
        # Rotation speed should be in expected range
        self.assertGreaterEqual(speed_1, 0.5)
        self.assertLessEqual(speed_1, 3.0)
        self.assertGreaterEqual(speed_2, 0.5)
        self.assertLessEqual(speed_2, 3.0)
    
    def test_lissajous_plasma_modulation(self):
        """Test that LissajousPlasma modulates plasma frequencies."""
        composite = LissajousPlasma(self.renderer)
        
        # Draw with different times
        composite.draw(0.0)
        freq_x_t0 = composite.target.freq_x
        
        composite.draw(math.pi)
        freq_x_t_pi = composite.target.freq_x
        
        # Frequencies should be in expected range
        self.assertGreaterEqual(freq_x_t0, 0.05)
        self.assertLessEqual(freq_x_t0, 0.15)
        self.assertGreaterEqual(freq_x_t_pi, 0.05)
        self.assertLessEqual(freq_x_t_pi, 0.15)
    
    def test_composite_update(self):
        """Test that composite update propagates to both animations."""
        composite = PlasmaLissajous(self.renderer)
        
        initial_source_t = composite.source.t
        initial_target_t = composite.target.t
        
        composite.update(1.0)
        
        # Both should be updated
        self.assertEqual(composite.source.t, initial_source_t + 1.0)
        self.assertEqual(composite.target.t, initial_target_t + 1.0)
    
    def test_composite_param_info(self):
        """Test that composites provide parameter info."""
        composite = PlasmaLissajous(self.renderer)
        
        info = composite.get_param_info()
        self.assertIsInstance(info, list)
        self.assertGreater(len(info), 0)
        
        # First item should show modulation strength
        self.assertIn("Mod:", info[0])


class TestCompositeIntegration(unittest.TestCase):
    """Integration tests for composite animations."""
    
    def setUp(self):
        """Set up test renderer."""
        self.renderer = Renderer()
    
    def test_all_composites_can_draw(self):
        """Test that all composites can draw without errors."""
        composites = [
            PlasmaLissajous(self.renderer),
            FluxSpiral(self.renderer),
            LissajousPlasma(self.renderer),
        ]
        
        for composite in composites:
            # Should not raise exception
            try:
                composite.draw(0.0)
                composite.update(0.016)
            except Exception as e:
                self.fail(f"{composite.__class__.__name__} failed to draw: {e}")
    
    def test_composites_run_multiple_frames(self):
        """Test that composites can run for multiple frames."""
        composite = PlasmaLissajous(self.renderer)
        
        # Simulate 60 frames
        for i in range(60):
            t = i * 0.016
            composite.update(0.016)
            composite.draw(t)
        
        # If we get here without exception, success
        self.assertTrue(True)


def main():
    """Run tests."""
    # Run with verbose output
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
