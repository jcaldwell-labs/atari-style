"""Tests for Lissajous Educational Series (Issue #29)."""

import math
from unittest.mock import patch

from atari_style.demos.visualizers.educational.lissajous_educational_series import (
    FREQUENCY_RATIOS, PHASE_STEPS, APPLICATIONS, GAME_ENEMIES, GALLERY_PATTERNS,
    draw_title_card, draw_info_overlay, draw_equation,
    generate_part1_intro_frames, generate_what_is_lissajous_frames,
    generate_equation_explanation_frames, generate_xy_visualization_frames,
    generate_part1_frames,
    generate_part2_intro_frames, generate_pattern_showcase_frames,
    generate_ratio_comparison_frames, generate_part2_frames,
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
    PreviewOptions, add_preview_watermark, filter_frames_for_preview,
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


class TestPart1Frames:
    """Tests for Part I frame generation."""

    def test_part1_intro_frames(self):
        """Verify Part I intro generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part1_intro_frames(canvas, fps=10))
        assert len(frames) > 0
        assert all(f.size == (canvas.img_width, canvas.img_height) for f in frames)

    def test_what_is_lissajous_frames(self):
        """Verify what is Lissajous explanation generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_what_is_lissajous_frames(canvas, fps))
        assert len(frames) == 6 * fps  # 6 seconds

    def test_equation_explanation_frames(self):
        """Verify equation explanation generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_equation_explanation_frames(canvas, fps))
        assert len(frames) == 8 * fps  # 8 seconds

    def test_xy_visualization_frames(self):
        """Verify L-shaped XY visualization generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_xy_visualization_frames(canvas, fps))
        assert len(frames) == 10 * fps  # 10 seconds

    def test_part1_full_generation(self):
        """Verify complete Part I generates."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part1_frames(canvas, fps=10))
        assert len(frames) > 200  # Should be substantial


class TestPart2Frames:
    """Tests for Part II frame generation."""

    def test_gallery_patterns_structure(self):
        """Verify gallery patterns have correct structure."""
        assert len(GALLERY_PATTERNS) >= 5
        for name, a, b, delta, description in GALLERY_PATTERNS:
            assert isinstance(name, str)
            assert isinstance(a, float)
            assert isinstance(b, float)
            assert isinstance(delta, (int, float))
            assert isinstance(description, str)

    def test_part2_intro_frames(self):
        """Verify Part II intro generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part2_intro_frames(canvas, fps=10))
        assert len(frames) > 0

    def test_pattern_showcase_frames(self):
        """Verify pattern showcase generates frames for each pattern."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_pattern_showcase_frames(canvas, fps))
        # 4 seconds per pattern
        expected = len(GALLERY_PATTERNS) * 4 * fps
        assert len(frames) == expected

    def test_ratio_comparison_frames(self):
        """Verify ratio comparison generates frames."""
        canvas = TerminalCanvas(cols=80, rows=24)
        fps = 10
        frames = list(generate_ratio_comparison_frames(canvas, fps))
        assert len(frames) == 8 * fps  # 8 seconds

    def test_part2_full_generation(self):
        """Verify complete Part II generates."""
        canvas = TerminalCanvas(cols=80, rows=24)
        frames = list(generate_part2_frames(canvas, fps=10))
        assert len(frames) > 200


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
        """Verify full series includes all 5 parts."""
        canvas = TerminalCanvas(cols=80, rows=24)
        # Use low fps to reduce frame count for test
        frames = list(generate_full_series_frames(canvas, fps=5))
        # Should have frames from title + parts 1,2,3,4,5 + credits
        assert len(frames) > 400  # 5 parts is substantial


class TestCLI:
    """Tests for CLI argument handling."""

    def test_cli_help(self):
        """Verify CLI module loads without errors."""
        from atari_style.demos.visualizers.educational import lissajous_educational_series
        assert hasattr(lissajous_educational_series, 'main')

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_part1(self, mock_render):
        """Verify CLI handles --part 1."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '-o', 'test.gif', '--fps', '5']
            result = main()
            assert result == 0
            assert mock_render.called
        finally:
            sys.argv = original_argv

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_part2(self, mock_render):
        """Verify CLI handles --part 2."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '2', '-o', 'test.gif', '--fps', '5']
            result = main()
            assert result == 0
            assert mock_render.called
        finally:
            sys.argv = original_argv

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


class TestCLIValidation:
    """Tests for CLI argument validation error handling."""

    def test_cli_negative_start_rejected(self):
        """Verify --start with negative value causes error."""
        import sys
        import pytest
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview', '--start', '-5', '-o', 'test.gif']
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
        finally:
            sys.argv = original_argv

    def test_cli_end_before_start_rejected(self):
        """Verify --end <= --start causes error."""
        import sys
        import pytest
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview',
                        '--start', '10', '--end', '5', '-o', 'test.gif']
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
        finally:
            sys.argv = original_argv

    def test_cli_end_equals_start_rejected(self):
        """Verify --end == --start causes error."""
        import sys
        import pytest
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview',
                        '--start', '5', '--end', '5', '-o', 'test.gif']
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
        finally:
            sys.argv = original_argv

    def test_cli_zero_duration_rejected(self):
        """Verify --duration 0 causes error."""
        import sys
        import pytest
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview', '--duration', '0', '-o', 'test.gif']
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
        finally:
            sys.argv = original_argv

    def test_cli_negative_duration_rejected(self):
        """Verify --duration with negative value causes error."""
        import sys
        import pytest
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview', '--duration', '-3', '-o', 'test.gif']
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
        finally:
            sys.argv = original_argv

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_time_args_without_preview_warns(self, mock_render, capsys):
        """Verify warning when --start/--end/--duration used without --preview."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            # Use --start without --preview
            sys.argv = ['prog', '--part', '1', '--start', '2.0', '-o', 'test.gif', '--fps', '5']
            result = main()
            assert result == 0

            # Verify warning was printed
            captured = capsys.readouterr()
            assert "Warning: --start, --end, and --duration are only used with --preview" in captured.out
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


class TestPreviewMode:
    """Tests for preview mode functionality (Issue #110)."""

    def test_preview_options_defaults(self):
        """Verify PreviewOptions has correct defaults."""
        opts = PreviewOptions()
        assert opts.enabled is False
        assert opts.fps == 5
        assert opts.start_time == 0.0
        assert opts.end_time is None
        assert opts.max_duration == 5.0

    def test_preview_options_custom(self):
        """Verify PreviewOptions accepts custom values."""
        opts = PreviewOptions(
            enabled=True,
            fps=10,
            start_time=5.0,
            end_time=15.0,
            max_duration=10.0
        )
        assert opts.enabled is True
        assert opts.fps == 10
        assert opts.start_time == 5.0
        assert opts.end_time == 15.0
        assert opts.max_duration == 10.0

    def test_add_preview_watermark(self):
        """Verify watermark is added to frame."""
        from PIL import Image
        # Create a simple test image (large enough for watermark)
        img = Image.new('RGB', (400, 200), color='blue')
        watermarked = add_preview_watermark(img)

        # Should return a new image (not modify in place)
        assert watermarked is not img
        # Should be same size
        assert watermarked.size == img.size

        # Verify watermark was added by checking for yellow pixels
        # The watermark text is drawn in yellow (255, 255, 0)
        pixels = list(watermarked.getdata())
        yellow_pixels = [p for p in pixels if p[0] > 200 and p[1] > 200 and p[2] < 50]
        assert len(yellow_pixels) > 0, "Watermark should contain yellow text pixels"

    def test_filter_frames_limits_duration(self):
        """Verify filter_frames_for_preview limits frame count with decimation."""
        canvas = TerminalCanvas(cols=40, rows=12)
        source_fps = 10
        preview_fps = 5  # 2:1 decimation

        # Generate 30 frames (3 seconds at 10 FPS)
        def generate_test_frames():
            for i in range(30):
                yield canvas.render()

        preview = PreviewOptions(enabled=True, fps=preview_fps, max_duration=1.0)
        filtered = list(filter_frames_for_preview(generate_test_frames(), source_fps, preview))

        # 1s at 10 FPS = 10 source frames, decimated 2:1 = 5 output frames
        assert len(filtered) == 5

    def test_filter_frames_start_time(self):
        """Verify filter_frames_for_preview respects start time with decimation."""
        canvas = TerminalCanvas(cols=40, rows=12)
        source_fps = 10
        preview_fps = 5  # 2:1 decimation

        # Generate 50 frames (5 seconds at 10 FPS)
        def generate_test_frames():
            for i in range(50):
                yield canvas.render()

        preview = PreviewOptions(
            enabled=True,
            fps=preview_fps,
            start_time=2.0,  # Start at 2s
            max_duration=1.0  # 1 second duration
        )
        filtered = list(filter_frames_for_preview(generate_test_frames(), source_fps, preview))

        # 1s at 10 FPS = 10 source frames, decimated 2:1 = 5 output frames
        assert len(filtered) == 5

    def test_filter_frames_start_end_range(self):
        """Verify filter_frames_for_preview respects start and end times with decimation."""
        canvas = TerminalCanvas(cols=40, rows=12)
        source_fps = 10
        preview_fps = 5  # 2:1 decimation

        # Generate 100 frames (10 seconds at 10 FPS)
        def generate_test_frames():
            for i in range(100):
                yield canvas.render()

        preview = PreviewOptions(
            enabled=True,
            fps=preview_fps,
            start_time=3.0,  # Start at 3s
            end_time=5.0     # End at 5s
        )
        filtered = list(filter_frames_for_preview(generate_test_frames(), source_fps, preview))

        # 2s at 10 FPS = 20 source frames, decimated 2:1 = 10 output frames
        assert len(filtered) == 10

    def test_filter_frames_adds_watermark(self):
        """Verify filtered frames have watermark."""
        canvas = TerminalCanvas(cols=40, rows=12)
        fps = 10

        def generate_test_frames():
            for i in range(10):
                yield canvas.render()

        preview = PreviewOptions(enabled=True, fps=5, max_duration=0.5)
        filtered = list(filter_frames_for_preview(generate_test_frames(), fps, preview))

        # With 10 FPS source, 5 FPS preview, decimation is 2:1
        # 0.5s at 10 FPS = 5 source frames, decimated to ~3 frames at 5 FPS
        # (5 frames / 2 decimation = 2.5, which yields frames 0, 2, 4 = 3 frames)
        assert len(filtered) == 3

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_preview_mode(self, mock_render):
        """Verify CLI handles --preview flag."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '1', '--preview', '-o', 'test.gif']
            result = main()
            assert result == 0
            assert mock_render.called
            # Check that FPS was set to 5 (preview default) using kwargs for robustness
            call_args = mock_render.call_args
            # render_gif(path, frames, fps) - check fps via position or keyword
            fps_arg = call_args.kwargs.get('fps') or call_args[0][2]
            assert fps_arg == 5
        finally:
            sys.argv = original_argv

    @patch('atari_style.demos.visualizers.educational.lissajous_educational_series.render_gif')
    def test_cli_preview_with_time_range(self, mock_render):
        """Verify CLI handles --preview with --start and --end."""
        mock_render.return_value = True
        import sys
        from atari_style.demos.visualizers.educational.lissajous_educational_series import main

        original_argv = sys.argv
        try:
            sys.argv = ['prog', '--part', '2', '--preview',
                        '--start', '5', '--end', '10', '-o', 'test.gif']
            result = main()
            assert result == 0
            assert mock_render.called
        finally:
            sys.argv = original_argv

    def test_filter_frames_decimates_for_fps_reduction(self):
        """Verify frames are decimated when preview FPS < source FPS.

        This test ensures correct playback speed: a 2-second segment at 15 FPS
        previewed at 5 FPS should yield 10 frames (not 30) to play back in 2s.
        """
        canvas = TerminalCanvas(cols=40, rows=12)
        source_fps = 15
        preview_fps = 5
        duration = 2.0  # 2 seconds

        # Generate 30 frames (2s at 15 FPS)
        def generate_frames():
            for _ in range(int(duration * source_fps)):
                yield canvas.render()

        preview = PreviewOptions(enabled=True, fps=preview_fps, max_duration=duration)
        filtered = list(filter_frames_for_preview(generate_frames(), source_fps, preview))

        # With decimation ratio of 3:1 (15/5), 30 source frames become 10 output frames
        # 10 frames at 5 FPS = 2 seconds - correct playback speed maintained
        expected_frames = int(duration * source_fps) // (source_fps // preview_fps)
        assert len(filtered) == expected_frames
        assert len(filtered) == 10  # 2s at 5 FPS

    def test_filter_frames_caps_preview_fps_to_source_fps(self, capsys):
        """Verify preview FPS > source FPS is capped with warning.

        When preview FPS exceeds source FPS, we can't create more frames than
        exist in the source. The function should cap to source FPS to maintain
        correct playback speed and print a warning.
        """
        canvas = TerminalCanvas(cols=40, rows=12)
        source_fps = 5
        preview_fps = 15  # Higher than source - should be capped
        duration = 2.0

        # Generate 10 frames (2s at 5 FPS)
        def generate_frames():
            for _ in range(int(duration * source_fps)):
                yield canvas.render()

        preview = PreviewOptions(enabled=True, fps=preview_fps, max_duration=duration)
        filtered = list(filter_frames_for_preview(generate_frames(), source_fps, preview))

        # Should yield all 10 source frames (capped to source FPS = no decimation)
        # 10 frames at 5 FPS = 2 seconds - correct playback speed maintained
        assert len(filtered) == 10

        # Verify warning was printed
        captured = capsys.readouterr()
        assert "Warning: Preview FPS (15) exceeds source FPS (5)" in captured.out
        assert "Capping preview FPS to source FPS" in captured.out
