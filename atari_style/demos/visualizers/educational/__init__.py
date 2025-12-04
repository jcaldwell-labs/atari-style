"""Educational math visualizers.

Interactive demonstrations of mathematical concepts:
- Unit circle and trigonometry
- Euler's formula and complex numbers
- Lissajous curves and parameter spaces

Video rendering:
    python -m atari_style.demos.visualizers.educational.unit_circle_educational
    python -m atari_style.demos.visualizers.educational.lissajous_terminal_gif --help

Interactive:
    python -m atari_style.demos.visualizers.educational.lissajous_explorer
"""

from .lissajous_explorer import run_lissajous_explorer
from .unit_circle_educational import render_unit_circle_educational

__all__ = [
    'run_lissajous_explorer',
    'render_unit_circle_educational',
]
