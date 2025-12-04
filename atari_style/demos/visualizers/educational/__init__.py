"""Educational math visualizers.

Interactive demonstrations of mathematical concepts:
- Unit circle and trigonometry
- Euler's formula and complex numbers
- Lissajous curves and parameter spaces

Video rendering:
    python -m atari_style.demos.visualizers.educational.unit_circle_educational
    python -m atari_style.demos.visualizers.educational.lissajous_terminal_gif --help
    python -m atari_style.demos.visualizers.educational.lissajous_educational_series --help

Interactive:
    python -m atari_style.demos.visualizers.educational.lissajous_explorer

Educational Series (Issue #29):
    Part III: Phase & Frequency Exploration
    Part IV: Real-World Applications
    Part V: The Game Demo
"""

from .lissajous_explorer import run_lissajous_explorer
from .unit_circle_educational import render_unit_circle_educational
from .lissajous_educational_series import (
    generate_part3_frames,
    generate_part4_frames,
    generate_part5_frames,
    generate_full_series_frames,
)

__all__ = [
    'run_lissajous_explorer',
    'render_unit_circle_educational',
    'generate_part3_frames',
    'generate_part4_frames',
    'generate_part5_frames',
    'generate_full_series_frames',
]
