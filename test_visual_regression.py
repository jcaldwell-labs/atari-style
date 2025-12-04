#!/usr/bin/env python3
"""Pytest integration for visual regression tests.

Run with:
    pytest test_visual_regression.py -v
    pytest test_visual_regression.py -v --save-diffs

Or standalone without pytest:
    python test_visual_regression.py
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest decorators for standalone execution
    class pytest:
        @staticmethod
        def fixture(func):
            return func
        @staticmethod
        def skip(msg):
            pass
        class mark:
            @staticmethod
            def skipif(condition, reason=""):
                def decorator(func):
                    return func
                return decorator
        @staticmethod
        def main(args):
            print("pytest not installed, running basic smoke test instead")
            print("Install pytest for full test suite: pip install pytest")
            return 0

try:
    from atari_style.core.visual_test import (
        VisualTestConfig,
        compare_baseline,
        generate_baseline,
    )
    VISUAL_TEST_AVAILABLE = True
except ImportError:
    VISUAL_TEST_AVAILABLE = False


@pytest.fixture
def visual_config(tmp_path):
    """Create a temporary visual test configuration."""
    baseline_dir = tmp_path / "baselines"
    diff_dir = tmp_path / "diffs"
    return VisualTestConfig(
        baseline_dir=baseline_dir,
        diff_dir=diff_dir,
        threshold=0.01,
        allow_antialiasing=True,
    )


@pytest.fixture
def demo_script():
    """Path to demo input script."""
    script_path = Path(__file__).parent / "scripts" / "demos" / "joystick-demo.json"
    if not script_path.exists():
        pytest.skip(f"Demo script not found: {script_path}")
    return str(script_path)


@pytest.mark.skipif(not VISUAL_TEST_AVAILABLE, reason="PIL/Pillow not available")
class TestVisualRegression:
    """Visual regression tests for terminal demos."""

    def test_joystick_test_baseline_generation(self, visual_config, demo_script):
        """Test generating baseline images for joystick_test demo."""
        success = generate_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            frames=[0, 5, 10],
            config=visual_config,
        )
        assert success, "Baseline generation failed"

        # Verify baseline files exist
        demo_dir = visual_config.baseline_dir / "joystick_test"
        assert demo_dir.exists(), "Baseline directory not created"
        assert (demo_dir / "metadata.json").exists(), "Metadata not created"
        assert (demo_dir / "frame_0000.png").exists(), "Frame 0 not created"
        assert (demo_dir / "frame_0005.png").exists(), "Frame 5 not created"
        assert (demo_dir / "frame_0010.png").exists(), "Frame 10 not created"

    def test_joystick_test_comparison_match(self, visual_config, demo_script):
        """Test comparing identical renders (should pass)."""
        # First generate baseline
        generate_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            frames=[0, 5],
            config=visual_config,
        )

        # Then compare (should match perfectly)
        results = compare_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            config=visual_config,
            save_diffs=False,
        )

        assert len(results) > 0, "No results returned"
        for result in results:
            assert result.passed, f"Frame {result.frame_number} failed: {result.error}"
            assert result.diff_ratio == 0.0, f"Expected perfect match, got diff={result.diff_ratio}"

    def test_missing_baseline(self, visual_config, demo_script):
        """Test behavior when baseline doesn't exist."""
        results = compare_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            config=visual_config,
        )

        assert len(results) == 1, "Should return single error result"
        assert not results[0].passed, "Should fail when baseline missing"
        assert results[0].error is not None, "Should have error message"

    def test_unknown_demo(self, visual_config, demo_script):
        """Test behavior with unknown demo name."""
        results = compare_baseline(
            demo_name='nonexistent_demo',
            script_path=demo_script,
            config=visual_config,
        )

        assert len(results) == 1, "Should return single error result"
        assert not results[0].passed, "Should fail for unknown demo"
        assert "Unknown demo" in results[0].error, "Should mention unknown demo"


@pytest.mark.skipif(not VISUAL_TEST_AVAILABLE, reason="PIL/Pillow not available")
class TestVisualDiff:
    """Test diff generation and visualization."""

    def test_diff_image_generation(self, visual_config, demo_script):
        """Test that diff images are generated on failure."""
        # Generate baseline
        generate_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            frames=[0],
            config=visual_config,
        )

        # Compare with save_diffs enabled
        results = compare_baseline(
            demo_name='joystick_test',
            script_path=demo_script,
            config=visual_config,
            save_diffs=True,
        )

        # Even on pass, diff should be saved if requested
        assert len(results) > 0, "No results returned"
        # Note: diff_image_path may be None if no diff, which is expected for identical renders


def test_cli_generate_command(tmp_path, demo_script):
    """Test CLI generate command (smoke test)."""
    if not VISUAL_TEST_AVAILABLE:
        pytest.skip("PIL/Pillow not available")

    import subprocess

    baseline_dir = tmp_path / "baselines"

    result = subprocess.run([
        sys.executable, '-m', 'atari_style.core.visual_test',
        'generate', 'joystick_test',
        '--script', demo_script,
        '--frames', '0,5',
        '--baseline-dir', str(baseline_dir),
    ], capture_output=True, text=True)

    # Should succeed
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert baseline_dir.exists(), "Baseline directory not created"


def test_cli_compare_command(tmp_path, demo_script):
    """Test CLI compare command (smoke test)."""
    if not VISUAL_TEST_AVAILABLE:
        pytest.skip("PIL/Pillow not available")

    import subprocess

    baseline_dir = tmp_path / "baselines"

    # First generate baseline
    subprocess.run([
        sys.executable, '-m', 'atari_style.core.visual_test',
        'generate', 'joystick_test',
        '--script', demo_script,
        '--frames', '0',
        '--baseline-dir', str(baseline_dir),
    ], check=True)

    # Then compare
    result = subprocess.run([
        sys.executable, '-m', 'atari_style.core.visual_test',
        'compare', 'joystick_test',
        '--script', demo_script,
        '--baseline-dir', str(baseline_dir),
    ], capture_output=True, text=True)

    # Should succeed (identical render)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "PASS" in result.stdout or "✓" in result.stdout, "Should show passing test"


if __name__ == '__main__':
    if PYTEST_AVAILABLE:
        pytest.main([__file__, '-v'])
    else:
        # Run basic smoke test
        print("Running basic visual regression smoke test...")
        print()
        
        if not VISUAL_TEST_AVAILABLE:
            print("SKIP: PIL/Pillow not available")
            sys.exit(0)
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Test configuration
            visual_config = VisualTestConfig(
                baseline_dir=tmp_path / "baselines",
                diff_dir=tmp_path / "diffs",
                threshold=0.01,
                allow_antialiasing=True,
            )
            
            # Test script path
            demo_script = str(Path(__file__).parent / "scripts" / "demos" / "joystick-demo.json")
            if not Path(demo_script).exists():
                print(f"SKIP: Demo script not found: {demo_script}")
                sys.exit(0)
            
            # Test 1: Generate baseline
            print("Test 1: Generate baseline...")
            success = generate_baseline(
                demo_name='joystick_test',
                script_path=demo_script,
                frames=[0, 5],
                config=visual_config,
            )
            assert success, "Baseline generation failed"
            print("  ✓ PASS")
            
            # Test 2: Compare (should match)
            print("Test 2: Compare identical renders...")
            results = compare_baseline(
                demo_name='joystick_test',
                script_path=demo_script,
                config=visual_config,
                save_diffs=False,
            )
            assert len(results) > 0, "No results returned"
            for result in results:
                assert result.passed, f"Frame {result.frame_number} failed"
                assert result.diff_ratio == 0.0, f"Expected perfect match"
            print("  ✓ PASS")
            
            # Test 3: Unknown demo
            print("Test 3: Unknown demo...")
            results = compare_baseline(
                demo_name='nonexistent_demo',
                script_path=demo_script,
                config=visual_config,
            )
            assert len(results) == 1, "Should return single error"
            assert not results[0].passed, "Should fail"
            assert "Unknown demo" in results[0].error
            print("  ✓ PASS")
            
        print()
        print("All smoke tests passed!")
        print("For full test suite, install pytest: pip install pytest")
