"""Tests for Lissajous Educational Series (Issue #29)."""

import math
from unittest.mock import patch, MagicMock

from atari_style.demos.visualizers.educational.lissajous_educational_series import (
    FREQUENCY_RATIOS, PHASE_STEPS, APPLICATIONS, GAME_ENEMIES,
    draw_title_card, draw_info_overlay, draw_equation,
    generate_part3_intro_frames, generate_phase_sweep_frames,
    generate_frequency_comparison_frames, generate_musical_intervals_frames,
    generate_part3_frames,
    generate_part4_intro_frames, generate_oscilloscope_demo_frames,
    generate_laser_show_frames, generate_harmonograph_frames,
    generate_part4_frames,
    generate_part5_intro_frames, generate_enemy_showcase_frames,
    generate_gameplay_demo_frames, generate_part5_frames,
    generate_series_title_frames, generate_series_credits_frames,
    generate_full_series_frames,
    GameEnemy,
)
from atari_style.demos.visualizers.educational.lissajous_terminal_gif import (
    TerminalCanvas,
)


class TestEducationalConstants:
    """Tests for educational constants and data."""

    def test_frequency_ratios_structure(self):
        """Verify frequency ratios have correct structure."""
        assert len(FREQUENCY_RATIOS) >= 5
        for ratio_name, a, b, description in FREQUENCY_RATIOS:
            assert isinstance(ratio_name, str)
            assert isinstance(a, float)
            assert isinstance(b, float)
            assert a > 0 and b > 0
            assert isinstance(description, str)

    def test_phase_steps_coverage(self):
        """Verify phase steps cover useful range."""
        assert len(PHASE_STEPS) >= 5
        phases = [step[0] for step in PHASE_STEPS]
        assert 0 in phases  # Start at 0
        assert any(abs(p - math.pi / 2) < 0.01 for p in phases)  # Include π/2

    def test_applications_variety(self):
        """Verify applications list has diverse entries."""
        assert len(APPLICATIONS) >= 4
        app_names = [app[0] for app in APPLICATIONS]
        assert "Oscilloscope" in app_names
        assert "Laser Shows" in app_names

    def test_game_enemies_attributes(self):
        """Verify game enemies have required attributes."""
        assert len(GAME_ENEMIES) >= 3
        for enemy in GAME_ENEMIES:
            assert isinstance(enemy, GameEnemy)
            assert enemy.a > 0 and enemy.b > 0
            assert enemy.speed > 0
            assert len(enemy.name) > 0
            assert len(enemy.color) > 0


class TestTitleAndOverlays:
    """Tests for title card and overlay rendering."""

    def test_draw_title_card_centered(self):
        """Verify title card draws without errors."""
        canvas = TerminalCanvas(cols=80, rows=24)
        draw_title_card(canvas, "TEST TITLE", "Subtitle text")
        # Should not raise

    def test_draw_info_overlay(self):
        """Verify info overlay draws correctly."""
        canvas = TerminalCanvas(cols=80, rows=24)
        lines = ["Line 1", "Line 2", "Line 3"]
        draw_info_overlay(canvas, lines, x=5, y=5)
        # Should not raise

    def test_draw_equation(self):
        """Verify equation rendering."""
        canvas = TerminalCanvas(cols=80, rows=24)
        draw_equation(canvas, y=10)
        # Should not raise


class TestPart3Frames:
    """Tests for Part III frame generation."""

    def test_part3_intro_frames(self):
        """Verify Part III intro generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part3_intro_frames(canvas, fps=10))
        assert len(frames) > 0
        assert all(f.size == (canvas.img_width, canvas.img_height) for f in frames)

    def test_phase_sweep_frames(self):
        """Verify phase sweep generates correct number of frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        # Duration is 8 seconds
        frames = list(generate_phase_sweep_frames(canvas, 1.0, 2.0, fps))
        assert len(frames) == 8 * fps  # 8 seconds at 10 fps

    def test_frequency_comparison_frames(self):
        """Verify frequency comparison generates frames for each ratio."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_frequency_comparison_frames(canvas, fps=10))
        # Should have frames for each ratio plus transitions
        assert len(frames) > len(FREQUENCY_RATIOS) * 10

    def test_musical_intervals_frames(self):
        """Verify musical intervals generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_musical_intervals_frames(canvas, fps=10))
        assert len(frames) > 0

    def test_part3_full_generation(self):
        """Verify complete Part III generates."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part3_frames(canvas, fps=10))
        assert len(frames) > 100  # Should be substantial


class TestPart4Frames:
    """Tests for Part IV frame generation."""

    def test_part4_intro_frames(self):
        """Verify Part IV intro generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part4_intro_frames(canvas, fps=10))
        assert len(frames) > 0

    def test_oscilloscope_demo_frames(self):
        """Verify oscilloscope demo generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_oscilloscope_demo_frames(canvas, fps))
        assert len(frames) == 6 * fps  # 6 seconds

    def test_laser_show_frames(self):
        """Verify laser show generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_laser_show_frames(canvas, fps=10))
        assert len(frames) > 0

    def test_harmonograph_frames(self):
        """Verify harmonograph generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_harmonograph_frames(canvas, fps))
        assert len(frames) == 5 * fps  # 5 seconds

    def test_part4_full_generation(self):
        """Verify complete Part IV generates."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part4_frames(canvas, fps=10))
        assert len(frames) > 100


class TestPart5Frames:
    """Tests for Part V frame generation."""

    def test_part5_intro_frames(self):
        """Verify Part V intro generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part5_intro_frames(canvas, fps=10))
        assert len(frames) > 0

    def test_enemy_showcase_frames(self):
        """Verify enemy showcase generates frames for each enemy."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_enemy_showcase_frames(canvas, fps))
        # 3 seconds per enemy
        expected = len(GAME_ENEMIES) * 3 * fps
        assert len(frames) == expected

    def test_gameplay_demo_frames(self):
        """Verify gameplay demo generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_gameplay_demo_frames(canvas, fps))
        assert len(frames) == 8 * fps  # 8 seconds

    def test_part5_full_generation(self):
        """Verify complete Part V generates."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part5_frames(canvas, fps=10))
        assert len(frames) > 100


class TestFullSeries:
    """Tests for full series generation."""

    def test_series_title_frames(self):
        """Verify series title generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_series_title_frames(canvas, fps=10))
        assert len(frames) == 3 * 10  # 3 seconds

    def test_series_credits_frames(self):
        """Verify credits generate frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_series_credits_frames(canvas, fps=10))
        assert len(frames) == 3 * 10  # 3 seconds

    def test_full_series_combines_all_parts(self):
        """Verify full series includes all components."""
        canvas = TerminalCanvas(cols=80, rows=24)
        # Use low fps to reduce frame count for test
        frames = list(generate_full_series_frames(canvas, fps=5))
        # Should have frames from title + parts 3,4,5 + credits
        assert len(frames) > 200


class TestCLI:
    """Tests for CLI argument handling."""

    def test_cli_help(self):
        """Verify CLI module loads without errors."""
        from atari_style.demos.visualizers.educational import lissajous_educational_series
        assert hasattr(lissajous_educational_series, 'main')

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_part3(self, mock_render):
        """Verify CLI handles --part 3."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '3', '-o', 'test.gif', '--fps', '5']
            result = main()
            assert result == 0
            assert mock_render.called
        finally:
            sys.argv = original_argv

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_full_series(self, mock_render):
        """Verify CLI handles --full-series."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--full-series', '-o', 'series.gif', '--fps', '5']
            result = main()
            assert result == 0
            assert mock_render.called
        finally:
            sys.argv = original_argv


class TestGameEnemy:
    """Tests for GameEnemy dataclass."""

    def test_game_enemy_creation(self):
        """Verify GameEnemy can be created."""
        enemy = GameEnemy(
            a=2.0, b=3.0, delta=math.pi / 4,
            name="TestEnemy", color="cyan", speed=1.5
        )
        assert enemy.a == 2.0
        assert enemy.b == 3.0
        assert enemy.name == "TestEnemy"

    def test_game_enemy_defaults(self):
        """Verify GameEnemy has sensible defaults."""
        enemy = GameEnemy(a=1.0, b=1.0, delta=0, name="Test", color="white")
        assert enemy.speed == 1.0  # Default speed
